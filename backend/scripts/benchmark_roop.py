"""Compare EXON-FACE vs Roop on the arcade gaming chair image."""
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


async def main():
    print("=" * 80)
    print("  EXON-FACE VS ROOP BENCHMARK COMPARISON")
    print("=" * 80)

    # 1. Paths to user uploaded files
    target_orig_path = Path(r"C:\Users\Bryan\.gemini\antigravity\brain\49593824-6799-4e70-95b9-0edc715a2223\.user_uploaded\media_1788397549433.jpg")
    roop_result_path = Path(r"C:\Users\Bryan\.gemini\antigravity\brain\49593824-6799-4e70-95b9-0edc715a2223\.user_uploaded\media_1788397457836.jpg")

    target_bgr = cv2.imread(str(target_orig_path))
    roop_bgr = cv2.imread(str(roop_result_path))

    if target_bgr is None or roop_bgr is None:
        print("[!] Error: No se pudieron cargar las imágenes del usuario.")
        return

    print(f"[*] Imagen original cargada: {target_bgr.shape}")
    print(f"[*] Imagen Roop cargada: {roop_bgr.shape}")

    # 2. Setup pipeline
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

    # Execute with high quality parameters
    params = RenderParams(
        identity_weight=1.0,
        wavelet_high_pass=1.0,
        codeformer_fidelity=0.80, # High fidelity to preserve Masiel's real features
        occlusion_masking=True,
    )

    print("[*] Ejecutando pipeline EXON-FACE...")
    job = await use_case.execute(
        job_id="arcade_masiel_benchmark",
        subject_id="julio",
        target_image_np=target_bgr,
        mode=RenderMode.EXPRESS,
        params=params,
    )

    print(f"[OK] Render completado: {job.output_path}")
    exon_bgr = cv2.imread(job.output_path)

    # Detect face crop box on original image to crop all 3
    crop_info = detector.detect_primary_face(target_bgr)
    x1, y1, x2, y2 = crop_info.bbox
    # Add generous padding for hair and lighting
    pad_h = int((y2 - y1) * 0.3)
    pad_w = int((x2 - x1) * 0.3)
    y1_p = max(0, y1 - pad_h)
    y2_p = min(target_bgr.shape[0], y2 + pad_h)
    x1_p = max(0, x1 - pad_w)
    x2_p = min(target_bgr.shape[1], x2 + pad_w)

    crop_orig = target_bgr[y1_p:y2_p, x1_p:x2_p]
    crop_roop = roop_bgr[y1_p:y2_p, x1_p:x2_p]
    crop_exon = exon_bgr[y1_p:y2_p, x1_p:x2_p]

    artifacts_dir = Path(r"C:\Users\Bryan\.gemini\antigravity\brain\49593824-6799-4e70-95b9-0edc715a2223")
    cv2.imwrite(str(artifacts_dir / "arcade_1_orig.png"), crop_orig)
    cv2.imwrite(str(artifacts_dir / "arcade_2_roop.png"), crop_roop)
    cv2.imwrite(str(artifacts_dir / "arcade_3_exon.png"), crop_exon)
    cv2.imwrite(str(artifacts_dir / "arcade_exon_full.png"), exon_bgr)

    print("\n[OK] Comparativas guardadas en artifacts:")
    print("  1. arcade_1_orig.png (Original Modelo)")
    print("  2. arcade_2_roop.png (Tu resultado previo con Roop)")
    print("  3. arcade_3_exon.png (Resultado EXON-FACE)")
    print("  4. arcade_exon_full.png (Resultado completo)")

if __name__ == "__main__":
    asyncio.run(main())
