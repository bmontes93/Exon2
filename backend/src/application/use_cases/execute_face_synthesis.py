"""Use Case: Execute Dual-Mode High-Fidelity Face Synthesis."""
import time
from typing import Callable, Optional
import numpy as np

from src.domain.entities import RenderJob, RenderParams, IdentityProfile
from src.domain.enums import AngleQuadrant, RenderMode, JobStatus
from src.domain.exceptions import FaceNotFoundException, DomainValidationError
from src.application.ports.face_detector import IFaceDetector
from src.application.ports.identity_extractor import IIdentityExtractor
from src.application.ports.neural_renderer import INeuralRenderer
from src.application.ports.face_parser import IFaceParser
from src.application.ports.image_blender import IImageBlender
from src.application.ports.face_enhancer import IFaceEnhancer
from src.infrastructure.memory.vram_orchestrator import VRAMOrchestrator
from src.infrastructure.storage.local_storage_adapter import LocalStorageAdapter
from src.infrastructure.storage.sqlite_metadata_repo import SQLiteMetadataRepo


class ExecuteFaceSynthesisUseCase:
    """
    Orchestrates the end-to-end neural face synthesis pipeline:
    1. Target 3D Pose and Landmark Detection
    2. Multi-Angle Identity Vector Matching
    3. Neural Generative Face Synthesis (VRAM guarded)
    4. Occlusion Masking & Segmentation
    5. Wavelet Frequency Texture Transfer (Anti-Plastic Skin)
    6. Facial Restoration (CodeFormer / GPEN)
    7. Full Image Re-compositing and Persistence
    """

    def __init__(
        self,
        storage_adapter: LocalStorageAdapter,
        metadata_repo: SQLiteMetadataRepo,
        face_detector: IFaceDetector,
        identity_extractor: IIdentityExtractor,
        neural_renderer: INeuralRenderer,
        face_parser: IFaceParser,
        image_blender: IImageBlender,
        face_enhancer: IFaceEnhancer,
        vram_orchestrator: VRAMOrchestrator,
    ):
        self.storage_adapter = storage_adapter
        self.metadata_repo = metadata_repo
        self.face_detector = face_detector
        self.identity_extractor = identity_extractor
        self.neural_renderer = neural_renderer
        self.face_parser = face_parser
        self.image_blender = image_blender
        self.face_enhancer = face_enhancer
        self.vram = vram_orchestrator

    async def execute(
        self,
        job_id: str,
        subject_id: str,
        target_image_np: np.ndarray,
        mode: RenderMode = RenderMode.EXPRESS,
        params: Optional[RenderParams] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> RenderJob:
        """Executes the dual synthesis pipeline asynchronously."""
        if params is None:
            params = RenderParams()

        # 1. Fetch Subject Identity Profile
        profile = self.metadata_repo.get_subject_profile(subject_id)
        if not profile:
            raise DomainValidationError(f"Subject '{subject_id}' not found in catalog")

        # 2. Initialize RenderJob record
        job = RenderJob(
            job_id=job_id,
            subject_id=subject_id,
            target_image_path=f"target_{job_id}.png",
            mode=mode,
            params=params,
        )
        self.metadata_repo.save_render_job(job)

        def _report_progress(step: str, progress: float):
            job.update_progress(step, progress)
            self.metadata_repo.update_render_job(job)
            if progress_callback:
                progress_callback(step, progress)

        try:
            # 3. Step 1: 3D Face Detection and Pose Estimation
            _report_progress("3D_DETECTION", 0.15)
            async with self.vram.acquire_slot("3D_DETECTION", estimated_mb=1200):
                target_crop = self.face_detector.detect_primary_face(target_image_np)

            x1, y1, x2, y2 = target_crop.bbox
            target_roi = target_image_np[y1:y2, x1:x2].copy()
            target_pose = target_crop.pose

            # 4. Step 2: Multi-Angle Identity Vector Matching
            _report_progress("IDENTITY_MATCHING", 0.30)
            chosen_quadrant = params.source_quadrant or target_pose.quadrant
            identity_emb = profile.get_closest_embedding(chosen_quadrant)

            # 5. Step 3: Neural Generative Synthesis (InSwapper Full Canvas)
            _report_progress("DIFFUSION_SYNTHESIS", 0.50)
            async with self.vram.acquire_slot("DIFFUSION_SYNTHESIS", estimated_mb=5800):
                swapped_full = self.neural_renderer.render_face_swap(
                    target_crop=target_roi,
                    identity_embedding=identity_emb,
                    target_pose=target_pose,
                    identity_weight=params.identity_weight,
                    full_image=target_image_np,
                    landmarks=target_crop.landmarks,
                    bbox=target_crop.bbox,
                )

            # 6. Step 4: Canonical 5-Point Umeyama Alignment & GPEN-512 Super-Resolution
            _report_progress("FACE_RESTORATION", 0.75)
            async with self.vram.acquire_slot("FACE_RESTORATION", estimated_mb=2100):
                import cv2
                from insightface.utils import face_align

                aligned_face, M = face_align.norm_crop2(
                    swapped_full, np.array(target_crop.landmarks, dtype=np.float32), 512
                )
                gpen_aligned = self.face_enhancer.enhance_face(
                    aligned_face, fidelity=params.codeformer_fidelity
                )
                # Blend 70% GPEN with 30% swapped for ultra natural smoothness without plastic look
                enhanced_aligned = (
                    gpen_aligned.astype(np.float32) * 0.70 + aligned_face.astype(np.float32) * 0.30
                ).astype(np.uint8)

            # 7. Step 5: Inverse Affine Canonical Warp & Seamless Composite
            _report_progress("OCCLUSION_MASKING", 0.90)
            async with self.vram.acquire_slot("OCCLUSION_MASKING", estimated_mb=1000):
                h_img, w_img = target_image_np.shape[:2]
                IM = cv2.invertAffineTransform(M)
                restored_full = cv2.warpAffine(
                    enhanced_aligned, IM, (w_img, h_img), borderMode=cv2.BORDER_REPLICATE
                )

                # Canonical feathered boundary mask
                mask_512 = np.ones((512, 512), dtype=np.float32)
                mask_512 = cv2.erode(mask_512, np.ones((15, 15), np.uint8))
                mask_512 = cv2.GaussianBlur(mask_512, (31, 31), 0)
                warp_mask = cv2.warpAffine(mask_512, IM, (w_img, h_img))
                warp_mask_3c = np.dstack([warp_mask] * 3)

                final_composite = (
                    restored_full.astype(np.float32) * warp_mask_3c
                    + swapped_full.astype(np.float32) * (1.0 - warp_mask_3c)
                ).astype(np.uint8)

            # 8. Step 6: High-Fidelity Inner Teeth Preservation (Only if mouth is open)
            if target_crop.landmark_2d_106 is not None:
                import cv2
                lmk = np.array(target_crop.landmark_2d_106, dtype=np.float32)
                mouth_height = np.linalg.norm(lmk[62] - lmk[60])
                if mouth_height > 2.5:
                    inner_indices = [65, 66, 62, 70, 61, 57, 60, 54]
                    inner_pts = np.array([lmk[i] for i in inner_indices], dtype=np.int32)
                    teeth_mask = np.zeros((h_img, w_img), dtype=np.float32)
                    cv2.fillPoly(teeth_mask, [inner_pts], 1.0)
                    teeth_mask = cv2.erode(teeth_mask, np.ones((3, 3), np.uint8))
                    teeth_mask = cv2.GaussianBlur(teeth_mask, (7, 7), 2)
                    teeth_mask_3c = np.dstack([teeth_mask] * 3)

                    final_composite = (
                        target_image_np.astype(np.float32) * teeth_mask_3c
                        + final_composite.astype(np.float32) * (1.0 - teeth_mask_3c)
                    ).astype(np.uint8)


            # 10. Step 8: Persist final output
            output_filename = f"render_{job_id}.png"
            try:
                import cv2
                success, encoded_img = cv2.imencode(".png", final_composite)
                if success:
                    png_bytes = encoded_img.tobytes()
                else:
                    raise ValueError()
            except Exception:
                from PIL import Image
                import io
                buf = io.BytesIO()
                Image.fromarray(final_composite).save(buf, format="PNG")
                png_bytes = buf.getvalue()

            output_path = self.storage_adapter.save_output_image(output_filename, png_bytes)

            job.complete(output_path=str(output_path))
            self.metadata_repo.update_render_job(job)
            if progress_callback:
                progress_callback("COMPLETED", 1.0)
            return job

        except Exception as e:
            job.fail(str(e))
            self.metadata_repo.update_render_job(job)
            raise e
