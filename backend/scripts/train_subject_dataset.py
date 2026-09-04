"""CLI script to scan, extract 3D landmarks, filter quality, and train identity profiles from a directory."""
import argparse
import sys
import time
from pathlib import Path
from PIL import Image
import numpy as np

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.domain.enums import AngleQuadrant
from src.infrastructure.adapters.pose_estimator_adapter import PoseEstimatorAdapter
from src.infrastructure.adapters.insightface_adapter import InsightFaceAdapter
from src.infrastructure.storage.local_storage_adapter import LocalStorageAdapter
from src.infrastructure.storage.sqlite_metadata_repo import SQLiteMetadataRepo
from src.application.use_cases.ingest_subject_dataset import (
    IngestSubjectDatasetUseCase,
    IngestInputImage,
)


def run_training(
    dataset_path: str,
    subject_id: str,
    name: str,
    max_images: int = 200,
    min_sharpness: float = 40.0,
    db_path: str = "exon_metadata.db",
):
    print("=" * 70)
    print("  EXON-FACE — MOTOR DE APRENDIZAJE Y CAPTURA 3D DE ROSTRO")
    print("=" * 70)
    print(f"[*] Directorio de Entrada : {dataset_path}")
    print(f"[*] ID del Sujeto          : {subject_id}")
    print(f"[*] Nombre                : {name}")
    print(f"[*] Límite de Fotos       : {max_images}")
    print(f"[*] Umbral de Nitidez     : {min_sharpness}")
    print("-" * 70)

    folder = Path(dataset_path)
    if not folder.exists() or not folder.is_dir():
        print(f"[!] Error: El directorio '{dataset_path}' no existe.")
        sys.exit(1)

    # 1. Gather image files
    all_files = list(folder.glob("*"))
    valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
    image_files = [f for f in all_files if f.suffix.lower() in valid_exts]
    total_found = len(image_files)
    print(f"[+] Archivos de imagen encontrados: {total_found}")

    if total_found == 0:
        print("[!] No se encontraron imágenes válidas.")
        sys.exit(1)

    selected_files = image_files[:max_images]
    print(f"[*] Procesando lote de {len(selected_files)} imágenes...")

    # 2. Initialize Services
    storage = LocalStorageAdapter(
        models_dir="models_cache",
        datasets_dir="datasets",
        outputs_dir="outputs",
    )
    repo = SQLiteMetadataRepo(db_path=db_path)
    detector = PoseEstimatorAdapter()
    embedder = InsightFaceAdapter()

    use_case = IngestSubjectDatasetUseCase(
        storage_adapter=storage,
        metadata_repo=repo,
        face_detector=detector,
        identity_extractor=embedder,
    )

    # 3. Read and format input images
    input_items = []
    print("[*] Leyendo y decodificando imágenes...")
    start_time = time.time()

    for idx, fpath in enumerate(selected_files, start=1):
        try:
            raw_bytes = fpath.read_bytes()
            with Image.open(fpath) as img:
                img_rgb = img.convert("RGB")
                img_np = np.array(img_rgb)

            input_items.append(
                IngestInputImage(
                    filename=fpath.name,
                    raw_bytes=raw_bytes,
                    image_np=img_np,
                )
            )
            if idx % 25 == 0 or idx == len(selected_files):
                print(f"    -> Leídas {idx}/{len(selected_files)} imágenes")
        except Exception as e:
            print(f"    [!] Error al leer '{fpath.name}': {e}")

    if not input_items:
        print("[!] No se pudo cargar ninguna imagen.")
        sys.exit(1)

    # 4. Execute Ingestion & Multi-Angle Training
    print("[*] Ejecutando detección 3D, filtrado laplaciano y extracción ArcFace...")
    result = use_case.execute(
        subject_id=subject_id,
        name=name,
        images=input_items,
        min_sharpness=min_sharpness,
    )

    elapsed = time.time() - start_time

    # 5. Summary Report
    print("=" * 70)
    print("  RESULTADOS DEL ENTRENAMIENTO Y CAPTURA 3D")
    print("=" * 70)
    print(f"[+] Sujeto Registrado     : {result.name} (ID: {result.subject_id})")
    print(f"[+] Total Procesadas      : {result.processed_count}")
    print(f"[+] Rostros 3D Válidos    : {result.valid_faces_count}")
    print(f"[+] Fotos Descartadas     : {result.discarded_count} (borrosas o sin rostro)")
    print(f"[+] Tiempo de Ejecución   : {elapsed:.2f} segundos ({elapsed/len(input_items):.3f}s por foto)")
    print("\n[+] Cuadrantes de Angulo 3D Cubiertos:")
    for quad in result.quadrants_covered:
        print(f"    [OK] {quad.value}")

    # Check in database
    profile = repo.get_subject_profile(subject_id)
    if profile:
        print("\n[+] Base de Datos SQLite sincronizada exitosamente:")
        print(f"    Ubicación: {Path(db_path).resolve()}")
        print(f"    Total de vectores de identidad: {len(profile.embeddings_by_quadrant)}")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EXON-FACE Dataset Ingestion & 3D Learning CLI")
    parser.add_argument("--path", type=str, default=r"Z:\MASIEL FOTOS\julio", help="Path to photos directory")
    parser.add_argument("--id", type=str, default="julio", help="Subject unique ID")
    parser.add_argument("--name", type=str, default="Julio", help="Subject full name")
    parser.add_argument("--limit", type=int, default=150, help="Maximum number of photos to process")
    parser.add_argument("--sharpness", type=float, default=20.0, help="Minimum Laplacian sharpness threshold")
    parser.add_argument("--db", type=str, default="exon_metadata.db", help="SQLite database path")

    args = parser.parse_args()
    run_training(
        dataset_path=args.path,
        subject_id=args.id,
        name=args.name,
        max_images=args.limit,
        min_sharpness=args.sharpness,
        db_path=args.db,
    )
