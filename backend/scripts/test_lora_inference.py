"""Test generating photorealistic portraits using Masiel's trained LoRA on RTX 3070."""
import os, sys, torch
from pathlib import Path
from PIL import Image

# Set cache
os.environ["HF_HOME"] = "D:/EXON2/models/huggingface"
os.environ["TORCH_HOME"] = "D:/EXON2/models/torch"

from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

def main():
    print("=" * 80)
    print("  EXON-FACE -- GENERACION DE PRUEBA CON LORA DE MASIEL")
    print("=" * 80)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    base_model_id = "runwayml/stable-diffusion-v1-5"
    lora_weights_dir = "D:/EXON2/models/loras/masiel_lora_weights"

    print(f"[*] Cargando pipeline base {base_model_id} en {device}...")
    pipe = StableDiffusionPipeline.from_pretrained(
        base_model_id,
        torch_dtype=torch.float16,
        safety_checker=None,
    ).to(device)

    # Use fast high-quality DPM-Solver
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)

    print(f"[*] Cargando adaptadores LoRA desde {lora_weights_dir}...")
    pipe.load_lora_weights(lora_weights_dir)

    artifacts_dir = Path(r"C:\Users\Bryan\.gemini\antigravity\brain\49593824-6799-4e70-95b9-0edc715a2223")

    # TEST 1: Arcade Theme (Matching user's benchmark image)
    print("\n[*] Generando Test 1: Retrato Arcade con luces de neón...")
    prompt_arcade = "cinematic portrait of ohwx woman in an arcade with blue and magenta neon lights, wearing black bustier, natural skin texture, authentic detailed eyes, high-end photography, 8k uhd, photorealistic, sharp focus"
    neg_prompt = "cartoon, 3d, painting, sketch, drawing, bad anatomy, bad eyes, disfigured, blurry, low resolution, plastic skin"

    generator = torch.Generator(device).manual_seed(1234)
    image_arcade = pipe(
        prompt_arcade,
        negative_prompt=neg_prompt,
        num_inference_steps=28,
        guidance_scale=7.0,
        generator=generator,
    ).images[0]

    out_1 = artifacts_dir / "masiel_lora_arcade.png"
    image_arcade.save(str(out_1))
    print(f"[OK] Imagen 1 guardada en: {out_1}")

    # TEST 2: Daytime Outdoor Portrait
    print("\n[*] Generando Test 2: Retrato Natural al aire libre...")
    prompt_outdoor = "outdoor close-up portrait of ohwx woman in natural golden hour sunlight, soft smile, detailed facial features, realistic skin pores, photorealistic, 8k uhd, dslr"
    
    generator2 = torch.Generator(device).manual_seed(5678)
    image_outdoor = pipe(
        prompt_outdoor,
        negative_prompt=neg_prompt,
        num_inference_steps=28,
        guidance_scale=7.0,
        generator=generator2,
    ).images[0]

    out_2 = artifacts_dir / "masiel_lora_outdoor.png"
    image_outdoor.save(str(out_2))
    print(f"[OK] Imagen 2 guardada en: {out_2}")

    print("\n======================================================================")
    print("  [OK] GENERACION DE PRUEBAS CON LORA COMPLETADA EXITOSAMENTE")
    print("======================================================================")

if __name__ == "__main__":
    main()
