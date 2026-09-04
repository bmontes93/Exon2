"""Automated downloader for official AI face synthesis models (ONNX & Hugging Face)."""
import os
import sys
import time
import urllib.request
from pathlib import Path


# Model Catalog: Tested verified official mirrors
MODELS_CATALOG = {
    "detection": {
        "name": "SCRFD 10G Face Detector (3D Keypoints)",
        "file": "det_10g.onnx",
        "subfolder": "detection",
        "urls": [
            "https://huggingface.co/public-data/insightface/resolve/main/models/buffalo_l/det_10g.onnx",
        ],
        "size_mb": 16.1,
    },
    "arcface": {
        "name": "ArcFace w600k (512-dim Identity Embedding)",
        "file": "w600k_r50.onnx",
        "subfolder": "insightface",
        "urls": [
            "https://huggingface.co/public-data/insightface/resolve/main/models/buffalo_l/w600k_r50.onnx",
        ],
        "size_mb": 166.3,
    },
    "swapper": {
        "name": "InSwapper 128 / 512 Core Neural Swapper",
        "file": "inswapper_128.onnx",
        "subfolder": "swappers",
        "urls": [
            "https://huggingface.co/ezioruan/inswapper_128.onnx/resolve/main/inswapper_128.onnx",
        ],
        "size_mb": 528.6,
    },
    "face_parser": {
        "name": "BiSeNet Face Parsing (Occlusion Segmentation)",
        "file": "parsing_bisenet.pth",
        "subfolder": "bisenet",
        "urls": [
            "https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/parsing_bisenet.pth",
        ],
        "size_mb": 50.8,
    },
    "codeformer": {
        "name": "CodeFormer Face Restoration",
        "file": "codeformer.pth",
        "subfolder": "codeformer",
        "urls": [
            "https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/codeformer.pth",
        ],
        "size_mb": 359.2,
    },
    "gpen_enhancer": {
        "name": "GPEN 512 Ultra Face Enhancer (ONNX)",
        "file": "GPEN-BFR-512.onnx",
        "subfolder": "codeformer",
        "urls": [
            "https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/facerestore_models/GPEN-BFR-512.onnx",
        ],
        "size_mb": 271.1,
    },
}


def download_file_with_progress(url: str, destination: Path, expected_mb: float) -> bool:
    """Downloads a file showing real-time progress and transfer speed."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_destination = destination.with_suffix(".download")

    print(f"[*] Descargando desde: {url}")
    print(f"[*] Destino: {destination}")

    start_time = time.time()
    last_print_time = start_time

    def reporthook(block_num, block_size, total_size):
        nonlocal last_print_time
        now = time.time()
        if now - last_print_time >= 0.5 or block_num * block_size >= total_size:
            downloaded = block_num * block_size
            percent = (downloaded / total_size) * 100 if total_size > 0 else 0
            downloaded_mb = downloaded / (1024 * 1024)
            speed = downloaded_mb / max(0.01, now - start_time)
            total_mb = total_size / (1024 * 1024) if total_size > 0 else expected_mb

            sys.stdout.write(
                f"\r    -> Progreso: [{percent:5.1f}%] {downloaded_mb:6.1f} / {total_mb:6.1f} MB  ({speed:5.2f} MB/s) "
            )
            sys.stdout.flush()
            last_print_time = now

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EXON-FACE Downloader"}
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=60) as response, open(temp_destination, "wb") as out_file:
            total_size = int(response.info().get("Content-Length", 0))
            downloaded = 0
            block_size = 1024 * 64  # 64 KB chunks

            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)
                reporthook(downloaded // block_size, block_size, total_size)

        print("\n    [OK] Descarga completada. Guardado.")
        if temp_destination.exists():
            if destination.exists():
                destination.unlink()
            temp_destination.rename(destination)
        return True
    except Exception as e:
        print(f"\n    [!] Error al descargar de {url}: {e}")
        if temp_destination.exists():
            temp_destination.unlink()
        return False


def main():
    root_models_dir = Path(r"D:\EXON2\models").resolve()
    root_models_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("  EXON-FACE — DESCARGADOR OFICIAL DE MODELOS PESADOS DE IA")
    print("=" * 70)
    print(f"[*] Carpeta de Modelos: {root_models_dir}\n")

    total_models = len(MODELS_CATALOG)
    success_count = 0

    for idx, (key, meta) in enumerate(MODELS_CATALOG.items(), start=1):
        target_path = root_models_dir / meta["subfolder"] / meta["file"]
        print(f"[{idx}/{total_models}] {meta['name']} (~{meta['size_mb']} MB)")

        if target_path.exists() and target_path.stat().st_size > 1024 * 1024:
            print(f"    [OK] Ya existe en disco ({target_path.stat().st_size / (1024*1024):.1f} MB). Omitiendo descarga.\n")
            success_count += 1
            continue

        downloaded = False
        for url in meta["urls"]:
            if download_file_with_progress(url, target_path, meta["size_mb"]):
                downloaded = True
                break

        if downloaded:
            success_count += 1
            print(f"    [OK] Guardado en: {target_path}\n")
        else:
            print(f"    [!] Fallaron todos los espejos para {meta['name']}\n")

    print("=" * 70)
    print(f"  RESUMEN: {success_count}/{total_models} MODELOS DISPONIBLES EN: {root_models_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
