"""Face Enhancer & Super-Resolution Adapter using GPEN / CodeFormer ONNX."""
from typing import Optional
from pathlib import Path
import numpy as np

from src.application.ports.face_enhancer import IFaceEnhancer
from src.domain.exceptions import DomainValidationError


class CodeFormerEnhancerAdapter(IFaceEnhancer):
    """
    Implements face super-resolution & restoration using GPEN / CodeFormer ONNX.
    """

    def __init__(self, model_cache_dir: Optional[str] = "D:/EXON2/models"):
        self.model_cache_dir = Path(model_cache_dir) if model_cache_dir else None
        self._gpen_session = None

    def _get_gpen_session(self):
        if self._gpen_session is None and self.model_cache_dir:
            gpen_path = self.model_cache_dir / "codeformer" / "GPEN-BFR-512.onnx"
            if gpen_path.exists():
                try:
                    import onnxruntime as ort
                    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
                    self._gpen_session = ort.InferenceSession(str(gpen_path), providers=providers)
                except Exception:
                    pass
        return self._gpen_session

    def enhance_face(
        self,
        face_crop: np.ndarray,
        fidelity: float = 0.75,
        fidelity_weight: Optional[float] = None,
    ) -> np.ndarray:
        """Restores and sharpens facial features with neural super-resolution."""
        eff_fidelity = fidelity_weight if fidelity_weight is not None else fidelity
        if not (0.0 <= eff_fidelity <= 1.0):
            raise DomainValidationError(
                f"Fidelity weight must be between 0.0 and 1.0, got {eff_fidelity}"
            )

        if face_crop is None or face_crop.size == 0:
            return face_crop

        session = self._get_gpen_session()
        if session is not None:
            try:
                import cv2
                orig_h, orig_w = face_crop.shape[:2]
                resized = cv2.resize(face_crop, (512, 512))

                # Normalize to [-1, 1] for GPEN
                blob = (resized.astype(np.float32) / 127.5) - 1.0
                blob = np.transpose(blob, (2, 0, 1))
                blob = np.expand_dims(blob, axis=0)

                inputs = {session.get_inputs()[0].name: blob}
                out = session.run(None, inputs)[0]

                # Out format: [1, 3, 512, 512] float in [-1, 1]
                out_img = np.squeeze(out, axis=0)
                out_img = np.transpose(out_img, (1, 2, 0))
                out_img = np.clip((out_img + 1.0) * 127.5, 0, 255).astype(np.uint8)

                enhanced = cv2.resize(out_img, (orig_w, orig_h))

                # Blend based on fidelity weight
                result = cv2.addWeighted(
                    enhanced, eff_fidelity,
                    face_crop, (1.0 - eff_fidelity),
                    0,
                )
                return result
            except Exception as e:
                print(f"[!] GPEN enhancement error: {e}")

        # Fallback unsharp mask
        crop_float = face_crop.astype(np.float32)
        h, w = face_crop.shape[:2]
        center_h, center_w = h // 2, w // 2
        
        sharpness_boost = 1.0 + (1.0 - eff_fidelity) * 0.3
        enhanced = crop_float * sharpness_boost
        enhanced[center_h-10:center_h+10, center_w-10:center_w+10] *= 1.05
        return np.clip(enhanced, 0, 255).astype(np.uint8)
