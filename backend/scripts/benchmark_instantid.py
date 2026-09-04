"""Benchmark InstantID Level 2 on arcade image with Masiel."""
import sys, os, cv2, torch
import numpy as np
from pathlib import Path
from PIL import Image

sys.path.insert(0, ".")
sys.path.insert(0, "src/infrastructure/adapters/instantid")

from diffusers import ControlNetModel
from diffusers.schedulers import EulerDiscreteScheduler
from insightface.app import FaceAnalysis
from pipeline_stable_diffusion_xl_instantid import StableDiffusionXLInstantIDPipeline

def draw_kps(image_pil, kps, color_list=[(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255)]):
    width, height = image_pil.size
    kps_canvas = np.zeros((height, width, 3), dtype=np.uint8)
    for idx, (x, y) in enumerate(kps):
        color = color_list[idx % len(color_list)]
        cv2.circle(kps_canvas, (int(x), int(y)), 10, color, -1)
    return Image.fromarray(kps_canvas)

def main():
    print("=" * 80)
    print("  EXON-FACE -- BENCHMARK NIVEL 2 (INSTANTID DIFUSIÓN 1024px)")
    print("=" * 80)

    # 1. Face Analysis for landmark detection & ArcFace embedding
    print("[*] 1/4 Extrayendo landmarks y embedding con InsightFace...")
    app = FaceAnalysis(name="buffalo_l", root="D:/EXON2/models", providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))

    # Source: Masiel
    source_bgr = cv2.imread(r"Z:\MASIEL FOTOS\julio\IMG_0020.JPG")
    source_faces = app.get(source_bgr)
    if not source_faces:
        print("[!] No face found in source image.")
        return
    source_face = source_faces[0]
    face_emb = source_face.normed_embedding

    # Target: Arcade photo
    target_path = r"C:\Users\Bryan\.gemini\antigravity\brain\49593824-6799-4e70-95b9-0edc715a2223\.user_uploaded\media_1788397549433.jpg"
    target_bgr = cv2.imread(target_path)
    target_faces = app.get(target_bgr)
    if not target_faces:
        print("[!] No face found in target image.")
        return
    target_face = target_faces[0]

    # Target PIL resized to 1024x1024
    target_pil = Image.fromarray(cv2.cvtColor(target_bgr, cv2.COLOR_BGR2RGB)).resize((1024, 1024))
    
    # Scale landmarks to 1024x1024
    orig_h, orig_w = target_bgr.shape[:2]
    scale_x = 1024.0 / orig_w
    scale_y = 1024.0 / orig_h
    kps_1024 = [[pt[0] * scale_x, pt[1] * scale_y] for pt in target_face.kps]
    control_image = draw_kps(target_pil, kps_1024)

    # 2. Setup InstantID Pipeline on RTX 3070
    print("\n[*] 2/4 Cargando pipeline SDXL-InstantID en NVIDIA RTX 3070...")
    controlnet = ControlNetModel.from_pretrained(
        "D:/EXON2/models/diffusion/InstantID/ControlNetModel",
        torch_dtype=torch.float16,
    )
    pipe = StableDiffusionXLInstantIDPipeline.from_pretrained(
        "D:/EXON2/models/diffusion/sdxl-base-1.0",
        controlnet=controlnet,
        torch_dtype=torch.float16,
    )
    pipe.load_ip_adapter_instantid("D:/EXON2/models/diffusion/InstantID/ip-adapter.bin")
    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
    pipe.enable_model_cpu_offload()

    # 3. Generate Image
    print("\n[*] 3/4 Generando síntesis difusa en resolución 1024x1024...")
    prompt = "film portrait of a young beautiful woman in an arcade with neon lights, detailed facial skin texture, realistic eyes, masterwork photograph, 8k"
    negative_prompt = "blurry, low quality, deformed, distorted, cartoon, plastic, doll, bad teeth, bad eyes"

    generator = torch.Generator("cuda").manual_seed(42)
    output = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image_embeds=face_emb,
        image=control_image,
        controlnet_conditioning_scale=0.8,
        ip_adapter_scale=0.8,
        num_inference_steps=25,
        guidance_scale=5.0,
        generator=generator,
    ).images[0]

    # 4. Save and crop comparison
    print("\n[*] 4/4 Guardando resultados...")
    artifacts_dir = Path(r"C:\Users\Bryan\.gemini\antigravity\brain\49593824-6799-4e70-95b9-0edc715a2223")
    full_path = artifacts_dir / "arcade_instantid_1024.png"
    output.save(str(full_path))
    print(f"[OK] Imagen 1024px guardada en: {full_path}")

    # Crop face area
    out_bgr = cv2.cvtColor(np.array(output), cv2.COLOR_RGB2BGR)
    # Target face bbox scaled to 1024
    bx1 = int(target_face.bbox[0] * scale_x)
    by1 = int(target_face.bbox[1] * scale_y)
    bx2 = int(target_face.bbox[2] * scale_x)
    by2 = int(target_face.bbox[3] * scale_y)
    pad = 40
    crop = out_bgr[max(0, by1-pad):min(1024, by2+pad), max(0, bx1-pad):min(1024, bx2+pad)]
    crop_path = artifacts_dir / "arcade_instantid_crop.png"
    cv2.imwrite(str(crop_path), crop)
    print(f"[OK] Crop guardado en: {crop_path}")

if __name__ == "__main__":
    main()
