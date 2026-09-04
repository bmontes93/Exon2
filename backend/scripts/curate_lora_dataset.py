"""Curate top 60 highest-quality photos of Masiel for LoRA training."""
import sys, os, cv2
from pathlib import Path
import numpy as np

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from insightface.app import FaceAnalysis

def calculate_sharpness(img_bgr):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())

def main():
    print("=" * 80)
    print("  EXON-FACE -- FASE 1: CURADURIA AUTOMATICA DE DATASET PARA LORA")
    print("=" * 80)

    input_dir = Path(r"Z:\MASIEL FOTOS\julio")
    output_dir = Path(r"D:\EXON2\datasets\masiel_lora")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Initialize FaceAnalysis
    print("[*] Inicializando detector SCRFD + ArcFace...")
    app = FaceAnalysis(name="buffalo_l", root="D:/EXON2/models", providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))

    # Reference photo to anchor Masiel's identity
    ref_img = cv2.imread(str(input_dir / "IMG_0020.JPG"))
    ref_faces = app.get(ref_img)
    if not ref_faces:
        print("[!] No se detectó rostro en la foto de referencia.")
        return
    ref_emb = ref_faces[0].normed_embedding
    print(f"[OK] Identidad base de Masiel anclada con vector de {len(ref_emb)} dimensiones.")

    # 2. Scan all photos
    print("\n[*] Escaneando fotografías en Z:\\MASIEL FOTOS\\julio...")
    all_files = [f for f in input_dir.glob("*") if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
    print(f"[*] Total de imágenes encontradas: {len(all_files)}")

    candidates = []
    
    # Process up to 500 candidate photos to select the best 60
    sample_files = all_files[::max(1, len(all_files) // 500)]
    print(f"[*] Muestreando lote de {len(sample_files)} imágenes para selección de élite...")

    for idx, fpath in enumerate(sample_files):
        img = cv2.imread(str(fpath))
        if img is None:
            continue

        faces = app.get(img)
        if not faces:
            continue

        for face in faces:
            # Check similarity to Masiel
            sim = float(np.dot(face.normed_embedding, ref_emb))
            if sim < 0.55:  # Skip people who are not Masiel
                continue

            x1, y1, x2, y2 = face.bbox.astype(int)
            fw = x2 - x1
            fh = y2 - y1

            if fw < 150 or fh < 150:  # Skip tiny faces
                continue

            # Calculate sharpness of face ROI
            h, w = img.shape[:2]
            x1_c = max(0, x1)
            y1_c = max(0, y1)
            x2_c = min(w, x2)
            y2_c = min(h, y2)
            face_roi = img[y1_c:y2_c, x1_c:x2_c]
            sharpness = calculate_sharpness(face_roi)

            if sharpness < 40.0:  # Skip blurry photos
                continue

            # Score = combination of similarity, sharpness and resolution
            score = (sim * 100.0) + min(100.0, sharpness * 0.5) + min(50.0, fw * 0.1)

            candidates.append({
                "path": fpath,
                "bbox": (x1, y1, x2, y2),
                "kps": face.kps,
                "score": score,
                "sharpness": sharpness,
                "sim": sim,
                "img": img,
            })

        if (idx + 1) % 50 == 0:
            print(f"    -> Analizadas {idx + 1}/{len(sample_files)} fotos | Candidatas válidas: {len(candidates)}")

    print(f"\n[OK] Análisis completado. Total de candidatas de alta calidad: {len(candidates)}")

    # 3. Sort by quality score and select top 60
    candidates.sort(key=lambda c: c["score"], reverse=True)
    selected = candidates[:60]
    print(f"[*] Seleccionadas las {len(selected)} mejores fotografías para el LoRA.")

    # 4. Crop, square center at 512x512 and generate captions
    for i, item in enumerate(selected):
        img = item["img"]
        h, w = img.shape[:2]
        x1, y1, x2, y2 = item["bbox"]
        
        # Center of face
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        
        # Crop size with 70% padding for hair, shoulders, and context
        box_size = int(max(x2 - x1, y2 - y1) * 1.7)
        
        crop_x1 = max(0, cx - box_size // 2)
        crop_y1 = max(0, cy - box_size // 2)
        crop_x2 = min(w, cx + box_size // 2)
        crop_y2 = min(h, cy + box_size // 2)
        
        crop = img[crop_y1:crop_y2, crop_x1:crop_x2]
        
        # Resize to square 512x512
        crop_512 = cv2.resize(crop, (512, 512), interpolation=cv2.INTER_LANCZOS4)
        
        img_name = f"masiel_{i+1:03d}.png"
        txt_name = f"masiel_{i+1:03d}.txt"
        
        cv2.imwrite(str(output_dir / img_name), crop_512)
        
        # Caption with activation token 'ohwx woman'
        caption = "a photo of ohwx woman, natural skin texture, realistic facial features, high quality portrait, 8k"
        with open(output_dir / txt_name, "w", encoding="utf-8") as f:
            f.write(caption)

    print(f"\n======================================================================")
    print(f"  [OK] FASE 1 COMPLETADA CON EXITO")
    print(f"  - Dataset curado en: {output_dir}")
    print(f"  - 60 fotos cuadradas en 512x512 con sus captions de texto.")
    print(f"======================================================================")

if __name__ == "__main__":
    main()
