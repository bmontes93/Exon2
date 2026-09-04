"""FaceFusion v3 Architecture: InSwapper + GPEN-512 + LAB Color Transfer + Dermal Texture Preservation + 106-point Anatomical Masking."""
import os, sys, cv2, torch
import numpy as np
from pathlib import Path
import onnxruntime as ort

# Add project root
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from insightface.app import FaceAnalysis
from insightface.model_zoo import get_model

def transfer_color_lab(source_bgr, target_bgr):
    """Transfer lighting and color distribution from target to source in LAB space."""
    src_lab = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    tgt_lab = cv2.cvtColor(target_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)

    s_mean = np.mean(src_lab.reshape(-1, 3), axis=0)
    s_std = np.std(src_lab.reshape(-1, 3), axis=0) + 1e-5
    t_mean = np.mean(tgt_lab.reshape(-1, 3), axis=0)
    t_std = np.std(tgt_lab.reshape(-1, 3), axis=0) + 1e-5

    # Scale and shift channels
    res_lab = (src_lab - s_mean) * (t_std / s_std) + t_mean
    res_lab = np.clip(res_lab, 0, 255).astype(np.uint8)
    return cv2.cvtColor(res_lab, cv2.COLOR_LAB2BGR)

def extract_high_pass_texture(image_bgr, ksize=9):
    """Extract fine high-frequency skin texture, pores, and specular reflections."""
    blurred = cv2.GaussianBlur(image_bgr, (ksize, ksize), 0)
    high_pass = image_bgr.astype(np.float32) - blurred.astype(np.float32)
    return high_pass

def run_gpen_onnx(session, face_bgr):
    """Run GPEN-BFR-512 super-resolution model."""
    h, w = face_bgr.shape[:2]
    inp = cv2.resize(face_bgr, (512, 512), interpolation=cv2.INTER_LANCZOS4)
    inp = inp.astype(np.float32)[:, :, ::-1] / 127.5 - 1.0  # BGR to RGB normalized [-1, 1]
    inp = np.transpose(inp, (2, 0, 1))[np.newaxis, ...]
    
    input_name = session.get_inputs()[0].name
    out = session.run(None, {input_name: inp})[0]
    out = np.clip((np.transpose(out[0], (1, 2, 0)) + 1.0) * 127.5, 0, 255).astype(np.uint8)
    out_bgr = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
    return cv2.resize(out_bgr, (w, h), interpolation=cv2.INTER_LANCZOS4)

def main():
    print("=" * 80)
    print("  EXON-FACE -- ARQUITECTURA FACEFUSION V3")
    print("=" * 80)

    # 1. Initialize FaceAnalysis & InSwapper
    print("[*] 1/5 Cargando modelos de InsightFace y GPEN...")
    app = FaceAnalysis(name="buffalo_l", root="D:/EXON2/models", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))

    swapper = get_model("D:/EXON2/models/swappers/inswapper_128.onnx", providers=["CPUExecutionProvider"])
    gpen_session = ort.InferenceSession("D:/EXON2/models/codeformer/GPEN-BFR-512.onnx", providers=["CPUExecutionProvider"])

    # 2. Load Source (Masiel) and Target (Arcade)
    source_bgr = cv2.imread(r"Z:\MASIEL FOTOS\julio\IMG_0020.JPG")
    target_path = r"C:\Users\Bryan\.gemini\antigravity\brain\49593824-6799-4e70-95b9-0edc715a2223\.user_uploaded\media_1788397549433.jpg"
    target_bgr = cv2.imread(target_path)

    source_faces = app.get(source_bgr)
    target_faces = app.get(target_bgr)

    if not source_faces or not target_faces:
        print("[!] Error detectando rostros.")
        return

    s_face = source_faces[0]
    t_face = target_faces[0]

    # 3. InSwapper Base Swap
    print("\n[*] 2/5 Realizando intercambio facial de identidad (InSwapper)...")
    swapped_full = swapper.get(target_bgr, t_face, s_face, paste_back=True)

    # 4. Color Matching in LAB space & Dermal Texture Injection
    print("\n[*] 3/5 Calibración de color adaptativa (LAB Color Transfer)...")
    x1, y1, x2, y2 = t_face.bbox.astype(int)
    h, w = target_bgr.shape[:2]
    pad = 25
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(w, x2 + pad)
    y2 = min(h, y2 + pad)

    target_roi = target_bgr[y1:y2, x1:x2]
    swapped_roi = swapped_full[y1:y2, x1:x2]

    # Enhance eyes/features with GPEN
    print("\n[*] 4/5 Restauración sub-píxel con GPEN-512...")
    gpen_enhanced = run_gpen_onnx(gpen_session, swapped_roi)
    # Blend 65% GPEN with 35% swapped for realistic skin softness
    enhanced_roi = (gpen_enhanced.astype(np.float32) * 0.70 + swapped_roi.astype(np.float32) * 0.30).astype(np.uint8)

    # Color match to scene lighting (neon purple/blue)
    color_matched_roi = transfer_color_lab(enhanced_roi, target_roi)

    # Dermal texture & pores injection
    texture_high_pass = extract_high_pass_texture(target_roi, ksize=9)
    textured_roi = np.clip(color_matched_roi.astype(np.float32) + 0.70 * texture_high_pass, 0, 255).astype(np.uint8)

    # Create smooth elliptical blending mask
    rh, rw = target_roi.shape[:2]
    mask = np.zeros((rh, rw), dtype=np.float32)
    center = (rw // 2, rh // 2)
    axes = (int(rw * 0.44), int(rh * 0.49))
    cv2.ellipse(mask, center, axes, 0, 0, 360, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (31, 31), 11)
    mask_3c = np.dstack([mask] * 3)

    blended_roi = (textured_roi.astype(np.float32) * mask_3c + target_roi.astype(np.float32) * (1.0 - mask_3c)).astype(np.uint8)

    final_result = target_bgr.copy()
    final_result[y1:y2, x1:x2] = blended_roi

    # 5. Inner Mouth & Teeth Preservation (106-point landmarks)
    print("\n[*] 5/5 Preservación anatómica dental (106-puntos)...")
    if hasattr(t_face, "landmark_2d_106") and t_face.landmark_2d_106 is not None:
        mouth_pts = t_face.landmark_2d_106[52:72].astype(int)
        mouth_mask = np.zeros(target_bgr.shape[:2], dtype=np.float32)
        cv2.fillPoly(mouth_mask, [mouth_pts], 1.0)
        mouth_mask = cv2.GaussianBlur(mouth_mask, (13, 13), 4)
        mouth_mask_3c = np.dstack([mouth_mask] * 3)
        final_result = (target_bgr.astype(np.float32) * mouth_mask_3c + final_result.astype(np.float32) * (1.0 - mouth_mask_3c)).astype(np.uint8)

    # Save artifacts
    artifacts_dir = Path(r"C:\Users\Bryan\.gemini\antigravity\brain\49593824-6799-4e70-95b9-0edc715a2223")
    out_full = artifacts_dir / "arcade_facefusion_v3.png"
    cv2.imwrite(str(out_full), final_result)
    print(f"\n[OK] Imagen completa guardada en: {out_full}")

    # Save crop
    crop = final_result[max(0, y1-15):min(h, y2+15), max(0, x1-15):min(w, x2+15)]
    crop_path = artifacts_dir / "arcade_facefusion_crop.png"
    cv2.imwrite(str(crop_path), crop)
    print(f"[OK] Crop guardado en: {crop_path}")

    # Side-by-side comparison with Roop
    roop_path = artifacts_dir / "arcade_2_roop.png"
    if roop_path.exists():
        roop_img = cv2.imread(str(roop_path))
        h_c, w_c = crop.shape[:2]
        roop_resized = cv2.resize(roop_img, (w_c, h_c))
        
        comp_roop = roop_resized.copy()
        comp_ff3 = crop.copy()
        cv2.putText(comp_roop, "ROOP (Plastico/Cera)", (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
        cv2.putText(comp_ff3, "EXON FACEFUSION V3 (Piel Real)", (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
        
        comparison = np.hstack([comp_roop, comp_ff3])
        comp_out = artifacts_dir / "comparison_roop_vs_ff3.png"
        cv2.imwrite(str(comp_out), comparison)
        print(f"[OK] Comparativa guardada en: {comp_out}")

if __name__ == "__main__":
    main()
