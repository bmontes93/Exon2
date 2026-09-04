"""Unit tests for ExecuteFaceSynthesisUseCase."""
import asyncio
import pytest
import numpy as np

from src.domain.entities import (
    IdentityProfile,
    RenderJob,
    RenderParams,
)
from src.domain.enums import AngleQuadrant, RenderMode, JobStatus
from src.infrastructure.adapters.pose_estimator_adapter import PoseEstimatorAdapter
from src.infrastructure.adapters.insightface_adapter import InsightFaceAdapter
from src.infrastructure.adapters.diffusers_renderer import DiffusersRendererAdapter
from src.infrastructure.adapters.bisenet_parser import BiSeNetParserAdapter
from src.infrastructure.adapters.wavelet_blender import WaveletBlenderAdapter
from src.infrastructure.adapters.codeformer_enhancer import CodeFormerEnhancerAdapter
from src.infrastructure.memory.vram_orchestrator import VRAMOrchestrator
from src.infrastructure.storage.local_storage_adapter import LocalStorageAdapter
from src.infrastructure.storage.sqlite_metadata_repo import SQLiteMetadataRepo
from src.application.use_cases.execute_face_synthesis import ExecuteFaceSynthesisUseCase


class TestExecuteFaceSynthesisUseCase:
    def test_execute_express_mode_synthesis_flow(self, tmp_path):
        async def run_test():
            storage = LocalStorageAdapter(
                models_dir=tmp_path / "models",
                datasets_dir=tmp_path / "datasets",
                outputs_dir=tmp_path / "outputs",
            )
            repo = SQLiteMetadataRepo(db_path=tmp_path / "metadata.db")
            detector = PoseEstimatorAdapter()
            embedder = InsightFaceAdapter()
            renderer = DiffusersRendererAdapter()
            parser = BiSeNetParserAdapter()
            blender = WaveletBlenderAdapter()
            enhancer = CodeFormerEnhancerAdapter()
            vram = VRAMOrchestrator()

            # Seed a subject in metadata
            profile = IdentityProfile(
                subject_id="subj_hero",
                name="Hero Subject",
                embeddings_by_quadrant={
                    AngleQuadrant.FRONTAL: [0.05] * 512,
                    AngleQuadrant.PROFILE_LEFT: [0.10] * 512,
                },
            )
            repo.save_subject_profile(profile)

            # Create target image (150x150 RGB)
            np.random.seed(42)
            target_np = np.random.randint(50, 200, (150, 150, 3), dtype=np.uint8)

            use_case = ExecuteFaceSynthesisUseCase(
                storage_adapter=storage,
                metadata_repo=repo,
                face_detector=detector,
                identity_extractor=embedder,
                neural_renderer=renderer,
                face_parser=parser,
                image_blender=blender,
                face_enhancer=enhancer,
                vram_orchestrator=vram,
            )

            progress_events = []

            def on_progress(step_name: str, progress: float):
                progress_events.append((step_name, progress))

            job = await use_case.execute(
                job_id="job_exp_001",
                subject_id="subj_hero",
                target_image_np=target_np,
                mode=RenderMode.EXPRESS,
                params=RenderParams(),
                progress_callback=on_progress,
            )

            assert job.status == JobStatus.COMPLETED
            assert job.progress == 1.0
            assert job.output_path is not None
            assert len(progress_events) >= 5

            # Verify persisted record in SQLite
            persisted_job = repo.get_render_job("job_exp_001")
            assert persisted_job is not None
            assert persisted_job.status == JobStatus.COMPLETED
            assert persisted_job.progress == 1.0

        asyncio.run(run_test())

    def test_execute_studio_pro_with_custom_weights(self, tmp_path):
        async def run_test():
            storage = LocalStorageAdapter(
                models_dir=tmp_path / "models",
                datasets_dir=tmp_path / "datasets",
                outputs_dir=tmp_path / "outputs",
            )
            repo = SQLiteMetadataRepo(db_path=tmp_path / "metadata.db")
            detector = PoseEstimatorAdapter()
            embedder = InsightFaceAdapter()
            renderer = DiffusersRendererAdapter()
            parser = BiSeNetParserAdapter()
            blender = WaveletBlenderAdapter()
            enhancer = CodeFormerEnhancerAdapter()
            vram = VRAMOrchestrator()

            profile = IdentityProfile(
                subject_id="subj_hero_2",
                name="Hero Subject 2",
                embeddings_by_quadrant={
                    AngleQuadrant.FRONTAL: [0.05] * 512,
                },
            )
            repo.save_subject_profile(profile)

            target_np = np.random.randint(50, 200, (120, 120, 3), dtype=np.uint8)

            use_case = ExecuteFaceSynthesisUseCase(
                storage_adapter=storage,
                metadata_repo=repo,
                face_detector=detector,
                identity_extractor=embedder,
                neural_renderer=renderer,
                face_parser=parser,
                image_blender=blender,
                face_enhancer=enhancer,
                vram_orchestrator=vram,
            )

            custom_params = RenderParams(
                identity_weight=1.4,
                wavelet_high_pass=1.8,
                codeformer_fidelity=0.85,
                occlusion_masking=True,
            )

            job = await use_case.execute(
                job_id="job_pro_002",
                subject_id="subj_hero_2",
                target_image_np=target_np,
                mode=RenderMode.STUDIO_PRO,
                params=custom_params,
            )

            assert job.status == JobStatus.COMPLETED
            assert job.params.identity_weight == 1.4
            assert job.params.wavelet_high_pass == 1.8

        asyncio.run(run_test())
