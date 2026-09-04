"""Download and verify SDXL-Lightning and InstantID models."""
import os
from pathlib import Path

# Direct cache to D:/EXON2/models/huggingface
os.environ["HF_HOME"] = "D:/EXON2/models/huggingface"
os.environ["TORCH_HOME"] = "D:/EXON2/models/torch"

from huggingface_hub import hf_hub_download, snapshot_download

def main():
    print("=" * 80)
    print("  EXON-FACE -- DESCARGA DE MODELOS GENERATIVOS SDXL & INSTANTID")
    print("=" * 80)
    
    models_dir = Path("D:/EXON2/models/diffusion")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    print("[*] 1/3 Descargando pesos de InstantID (ControlNet + IP-Adapter)...")
    snapshot_download(
        repo_id="InstantX/InstantID",
        local_dir="D:/EXON2/models/diffusion/InstantID",
        allow_patterns=["*controlnet*", "*ip-adapter*", "*.json"],
    )
    print("[OK] InstantID descargado.")

    print("\n[*] 2/3 Descargando SDXL-Lightning 4-step UNet (Inferencia Ultra-Rápida)...")
    hf_hub_download(
        repo_id="ByteDance/SDXL-Lightning",
        filename="sdxl_lightning_4step_unet.safetensors",
        local_dir="D:/EXON2/models/diffusion/SDXL-Lightning",
    )
    print("[OK] SDXL-Lightning descargado.")

    print("\n[OK] Modelos de difusión preparados en D:/EXON2/models/diffusion")

if __name__ == "__main__":
    main()
