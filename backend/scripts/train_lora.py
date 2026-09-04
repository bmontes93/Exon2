"""Train Masiel LoRA using PyTorch CUDA, Diffusers, and PEFT on RTX 3070."""
import os, sys, math, time
from pathlib import Path
from PIL import Image
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

# Set cache directories
os.environ["HF_HOME"] = "D:/EXON2/models/huggingface"
os.environ["TORCH_HOME"] = "D:/EXON2/models/torch"

from transformers import CLIPTokenizer, CLIPTextModel
from diffusers import AutoencoderKL, UNet2DConditionModel, DDPMScheduler
from peft import LoraConfig, get_peft_model

class MasielLoraDataset(Dataset):
    def __init__(self, data_dir: Path, tokenizer, size=512):
        self.data_dir = data_dir
        self.tokenizer = tokenizer
        self.size = size
        
        self.images = sorted(list(data_dir.glob("*.png")))
        print(f"[*] Dataset cargado: {len(self.images)} imágenes.")
        
        self.transform = transforms.Compose([
            transforms.Resize((size, size), interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.ToTensor(),
            transforms.Normalize([0.5], [0.5]),
        ])

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path = self.images[idx]
        image = Image.open(img_path).convert("RGB")
        pixel_values = self.transform(image)
        
        txt_path = img_path.with_suffix(".txt")
        if txt_path.exists():
            with open(txt_path, "r", encoding="utf-8") as f:
                prompt = f.read().strip()
        else:
            prompt = "a photo of ohwx woman, high quality portrait"
            
        inputs = self.tokenizer(
            prompt,
            padding="max_length",
            max_length=self.tokenizer.model_max_length,
            truncation=True,
            return_tensors="pt",
        )
        input_ids = inputs.input_ids[0]
        
        return {"pixel_values": pixel_values, "input_ids": input_ids}

def main():
    print("=" * 80)
    print("  EXON-FACE -- FASE 2: ENTRENAMIENTO DE LORA (NVIDIA RTX 3070)")
    print("=" * 80)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Dispositivo de cómputo: {device}")
    if torch.cuda.is_available():
        print(f"[*] GPU: {torch.cuda.get_device_name(0)}")
        print(f"[*] VRAM disponible: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

    base_model_id = "runwayml/stable-diffusion-v1-5"
    output_dir = Path("D:/EXON2/models/loras")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[*] 1/4 Descargando y cargando modelo base {base_model_id}...")
    tokenizer = CLIPTokenizer.from_pretrained(base_model_id, subfolder="tokenizer")
    text_encoder = CLIPTextModel.from_pretrained(base_model_id, subfolder="text_encoder", torch_dtype=torch.float16).to(device)
    vae = AutoencoderKL.from_pretrained(base_model_id, subfolder="vae", torch_dtype=torch.float16).to(device)
    unet = UNet2DConditionModel.from_pretrained(base_model_id, subfolder="unet", torch_dtype=torch.float16).to(device)
    noise_scheduler = DDPMScheduler.from_pretrained(base_model_id, subfolder="scheduler")

    # Freeze base models
    text_encoder.requires_grad_(False)
    vae.requires_grad_(False)
    unet.requires_grad_(False)

    print("\n[*] 2/4 Inyectando adaptadores LoRA (Rank=16, Alpha=32)...")
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["to_k", "to_q", "to_v", "to_out.0"],
        lora_dropout=0.05,
        bias="none",
    )
    unet = get_peft_model(unet, lora_config)
    unet.print_trainable_parameters()

    # Enable gradient checkpointing to keep VRAM < 6GB
    unet.enable_gradient_checkpointing()

    # 3. Dataset and DataLoader
    data_dir = Path(r"D:\EXON2\datasets\masiel_lora")
    dataset = MasielLoraDataset(data_dir, tokenizer, size=512)
    train_dataloader = DataLoader(dataset, batch_size=1, shuffle=True)

    # 4. Training Hyperparameters
    num_train_epochs = 16  # 60 images * 16 epochs = 960 steps
    learning_rate = 1e-4
    optimizer = torch.optim.AdamW(unet.parameters(), lr=learning_rate, weight_decay=1e-2)

    total_steps = len(train_dataloader) * num_train_epochs
    print(f"\n[*] 3/4 Iniciando entrenamiento en GPU...")
    print(f"    -> Total épocas: {num_train_epochs}")
    print(f"    -> Pasos totales: {total_steps}")
    print(f"    -> Learning rate: {learning_rate}")

    unet.train()
    global_step = 0
    start_time = time.time()

    for epoch in range(num_train_epochs):
        epoch_loss = 0.0
        for step, batch in enumerate(train_dataloader):
            optimizer.zero_grad()

            # Latent encoding with VAE (in fp16)
            pixel_values = batch["pixel_values"].to(device, dtype=torch.float16)
            with torch.no_grad():
                latents = vae.encode(pixel_values).latent_dist.sample()
                latents = latents * vae.config.scaling_factor

            # Sample random noise
            noise = torch.randn_like(latents)
            timesteps = torch.randint(0, noise_scheduler.config.num_train_timesteps, (latents.shape[0],), device=device).long()
            noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)

            # Text embeddings
            with torch.no_grad():
                encoder_hidden_states = text_encoder(batch["input_ids"].to(device))[0]

            # Predict the noise residual (with LoRA)
            noise_pred = unet(noisy_latents, timesteps, encoder_hidden_states).sample

            # Compute loss
            loss = F.mse_loss(noise_pred.float(), noise.float(), reduction="mean")
            loss.backward()

            torch.nn.utils.clip_grad_norm_(unet.parameters(), 1.0)
            optimizer.step()

            epoch_loss += loss.item()
            global_step += 1

            if global_step % 50 == 0 or global_step == total_steps:
                elapsed = time.time() - start_time
                steps_per_sec = global_step / max(1, elapsed)
                remaining_sec = (total_steps - global_step) / max(0.1, steps_per_sec)
                print(f"    [Paso {global_step:03d}/{total_steps}] Loss: {loss.item():.4f} | Vel: {steps_per_sec:.2f} it/s | Restante: {int(remaining_sec//60)}m {int(remaining_sec%60)}s")

    print("\n[*] 4/4 Guardando pesos de LoRA en formato SafeTensors...")
    save_path = output_dir / "masiel_lora.safetensors"
    unet.save_pretrained(output_dir / "masiel_lora_weights")
    
    # Save standalone safetensors
    from safetensors.torch import save_file
    state_dict = unet.state_dict()
    # Filter only lora keys
    lora_dict = {k: v.cpu().half() for k, v in state_dict.items() if "lora" in k}
    save_file(lora_dict, str(save_path))

    total_time = time.time() - start_time
    print(f"\n======================================================================")
    print(f"  [OK] ENTRENAMIENTO DE LORA COMPLETADO CON EXITO!")
    print(f"  - Archivo LoRA: {save_path}")
    print(f"  - Tamaño: {save_path.stat().st_size / 1e6:.2f} MB")
    print(f"  - Tiempo total: {int(total_time//60)} minutos {int(total_time%60)} segundos")
    print(f"======================================================================")

if __name__ == "__main__":
    main()
