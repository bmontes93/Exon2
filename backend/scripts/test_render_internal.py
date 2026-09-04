"""End-to-end internal test of face synthesis pipeline."""
import sys
import asyncio
from pathlib import Path
import cv2
import numpy as np

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.domain.entities import RenderParams
from src.domain.enums import RenderMode
from src.infrastructure.memory.vram_orchestrator import VRAMOrchestrator
from src.infrastructure.storage.local_storage_adapter import LocalStorageAdapter
from src.infrastructure.storage.sqlite_metadata_repo import SQLiteMetadataRepo
from src.infrastructure.adapters.pose_estimator_adapter import PoseEstimatorAdapter
from src.infrastructure.adapters.insightface_adapter import InsightFaceAdapter
from src.infrastructure.adapters.diffusers_renderer import DiffusersRendererAdapter
from src.infrastructure.adapters.bisenet_parser import BiSeNetParserAdapter
from src.infrastructure.adapters.wavelet_blender import WaveletBlenderAdapter
from src.infrastructure.adapters.codeformer_enhancer import CodeFormerEnhancerAdapter
from src.application.use_cases.execute_face_synthesis import ExecuteFaceSynthesisUseCase


async def run_internal_test():
    print("=" * 70)
    print("  EXON-FACE — PRUEBA INTERNA DIRECTA DE SÍNTESIS FACIAL")
    print("=" * 70)

    # 1. Target image
    target_path = Path("outputs/render_job_fe03b1c628.png")
    if not target_path.exists():
        # Fallback to any image
        target_path = Path(r"Z:\MASIEL FOTOS\julio\IMG_0025.JPG")
    
    print(f"[*] Imagen Destino: {target_path}")
    target_bgr = cv2.imread(str(target_path))
    if target_bgr is None:
        print("[!] Error leyendo imagen destino.")
        return

    print(f"[*] Dimensiones imagen destino: {target_bgr.shape}")

    # 2. Setup adapters
    models_dir = "D:/EXON2/models"
    storage = LocalStorageAdapter(models_dir=models_dir, datasets_dir="datasets", outputs_dir="outputs")
    repo = SQLiteMetadataRepo("exon_metadata.db")
    vram = VRAMOrchestrator()
    detector = PoseEstimatorAdapter(model_cache_dir=models_dir)
    embedder = InsightFaceAdapter(model_path=models_dir)
    renderer = DiffusersRendererAdapter(model_cache_dir=models_dir)
    parser = BiSeNetParserAdapter()
    blender = WaveletBlenderAdapter()
    enhancer = CodeFormerEnhancerAdapter(model_cache_dir=models_dir)

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

    params = RenderParams(
        identity_weight=1.0,
        wavelet_high_pass=1.0,
        codeformer_fidelity=0.75,
        occlusion_masking=True,
    )

    def progress_cb(step, prog):
        print(f"    -> [Progreso {int(prog*100)}%] Fase: {step}")

    print("\n[*] Ejecutando ExecuteFaceSynthesisUseCase para sujeto 'julio'...")
    try:
        job = await use_case.execute(
            job_id="test_internal_swap",
            subject_id="julio",
            target_image_np=target_bgr,
            mode=RenderMode.EXPRESS,
            params=params,
            progress_callback=progress_cb,
        )
        print("\n[OK] Job Completado con Éxito!")
        print(f"[*] Archivo de salida generado: {job.output_path}")

        # Compare output with target
        out_bgr = cv2.imread(job.output_path)
        if out_bgr is not None:
            diff = np.abs(out_bgr.astype(float) - target_bgr.astype(float)).sum(axis=2)
            max_diff = np.max(diff)
            changed_pixels = np.sum(diff > 5)
            print(f"[*] Píxeles modificados significativamente (>5): {changed_pixels}")
            print(f"[*] Diferencia máxima en canal de color: {max_diff}")

            # Crop face area of original and output to inspect
            y_indices, x_indices = np.where(diff > 5)
            if len(y_indices) > 0:
                y1, y2 = max(0, y_indices.min() - 20), min(target_bgr.shape[0], y_indices.max() + 20)
                x1, x2 = max(0, x_indices.min() - 20), min(target_bgr.shape[1], x_indices.max() + 20)
                cv2.imwrite("outputs/crop_before.png", target_bgr[y1:y2, x1:x2])
                cv2.imwrite("outputs/crop_after_julio.png", out_bgr[y1:y2, x1:x2])
                print("[*] Guardadas comparativas en:")
                print("    - outputs/crop_before.png")
                print("    - outputs/crop_after_julio.png")
            else:
                print("[!] ADVERTENCIA: No hubo cambios de píxeles en la imagen de salida.")
        else:
            print("[!] Error: No se pudo leer la imagen de salida generada.")

    except Exception as e:
        import traceback
        print(f"\n[!] ERROR DURANTE EL PIPELINE:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_internal_test())
