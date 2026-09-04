"""Batch test 3 uploaded photos using Option A (Natural Eye & Teeth Preservation + Aligned GPEN)."""
import os, sys, cv2
import numpy as np
from pathlib import Path
import onnxruntime as ort

from insightface.app import FaceAnalysis
from insightface.model_zoo import get_model
from insightface.utils import face_align

def process_image(target_path: Path, source_img: np.ndarray, app: FaceAnalysis, swapper, gpen_session, out_path: Path, crop_path: Path):
    print(f"\n[*] Procesando: {target_path.name}...")
    target_img = cv2.imread(str(target_path))
    if target_img is None:
        print(f"[!] No se pudo cargar {target_path}")
        return

    h, w = target_img.shape[:2]

    # Detect faces
    t_faces = app.get(target_img)
    s_faces = app.get(source_img)

    if not t_faces or not s_faces:
        print("[!] No se detectó rostro en target o source.")
        return

    t_face = t_faces[0]
    s_face = s_faces[0]

    # 1. Full Image InSwapper
    swapped_full = swapper.get(target_img, t_face, s_face, paste_back=True)

    # 2. Aligned GPEN-512 enhancement
    aligned_face, M = face_align.norm_crop2(swapped_full, t_face.kps, 512)
    inp = aligned_face.astype(np.float32)[:, :, ::-1] / 127.5 - 1.0
    inp = np.transpose(inp, (2, 0, 1))[np.newaxis, ...]
    input_name = gpen_session.get_inputs()[0].name
    out = gpen_session.run(None, {input_name: inp})[0]
    out = np.clip((np.transpose(out[0], (1, 2, 0)) + 1.0) * 127.5, 0, 255).astype(np.uint8)
    out_bgr = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)

    # Blend 70% GPEN with 30% swapped for realistic skin softness
    enhanced_aligned = (out_bgr.astype(np.float32) * 0.70 + aligned_face.astype(np.float32) * 0.30).astype(np.uint8)

    # 3. Inverse warp back to full canvas
    IM = cv2.invertAffineTransform(M)
    restored_full = cv2.warpAffine(enhanced_aligned, IM, (w, h), borderMode=cv2.BORDER_REPLICATE)

    # 4. Canonical Face Mask
    mask_512 = np.ones((512, 512), dtype=np.float32)
    mask_512 = cv2.erode(mask_512, np.ones((15, 15), np.uint8))
    mask_512 = cv2.GaussianBlur(mask_512, (31, 31), 0)
    warp_mask = cv2.warpAffine(mask_512, IM, (w, h))
    warp_mask_3c = np.dstack([warp_mask] * 3)

    final_composite = (restored_full.astype(np.float32) * warp_mask_3c + swapped_full.astype(np.float32) * (1.0 - warp_mask_3c)).astype(np.uint8)

    # 5. Inner Teeth & Cavity Preservation (Only if mouth is open)
    if hasattr(t_face, "landmark_2d_106") and t_face.landmark_2d_106 is not None:
        lmk = t_face.landmark_2d_106.astype(np.float32)
        mouth_height = np.linalg.norm(lmk[62] - lmk[60])
        if mouth_height > 2.5:
            inner_indices = [65, 66, 62, 70, 61, 57, 60, 54]
            inner_pts = np.array([lmk[i] for i in inner_indices], dtype=np.int32)
            teeth_mask = np.zeros((h, w), dtype=np.float32)
            cv2.fillPoly(teeth_mask, [inner_pts], 1.0)
            teeth_mask = cv2.erode(teeth_mask, np.ones((3, 3), np.uint8))
            teeth_mask = cv2.GaussianBlur(teeth_mask, (7, 7), 2)
            teeth_mask_3c = np.dstack([teeth_mask] * 3)

            final_composite = (target_img.astype(np.float32) * teeth_mask_3c + final_composite.astype(np.float32) * (1.0 - teeth_mask_3c)).astype(np.uint8)


    # Save full result
    cv2.imwrite(str(out_path), final_composite)
    print(f"[OK] Guardado full: {out_path.name}")

    # Save zoom crop
    bx1, by1, bx2, by2 = t_face.bbox.astype(int)
    pad = int((by2 - by1) * 0.25)
    crop = final_composite[max(0, by1-pad):min(h, by2+pad), max(0, bx1-pad):min(w, bx2+pad)]
    cv2.imwrite(str(crop_path), crop)
    print(f"[OK] Guardado crop: {crop_path.name}")

def main():
    print("=" * 80)
    print("  EXON-FACE -- PROCESAMIENTO POR LOTES: 3 FOTOS (OPCION A)")
    print("=" * 80)

    # Setup InsightFace & Models
    app = FaceAnalysis(name="buffalo_l", root="D:/EXON2/models", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))

    swapper = get_model("D:/EXON2/models/swappers/inswapper_128.onnx", providers=["CPUExecutionProvider"])
    gpen_session = ort.InferenceSession("D:/EXON2/models/codeformer/GPEN-BFR-512.onnx", providers=["CPUExecutionProvider"])

    source_img = cv2.imread(r"Z:\MASIEL FOTOS\julio\IMG_0020.JPG")
    
    user_upload_dir = Path(r"C:\Users\Bryan\.gemini\antigravity\brain\49593824-6799-4e70-95b9-0edc715a2223\.user_uploaded")
    artifacts_dir = Path(r"C:\Users\Bryan\.gemini\antigravity\brain\49593824-6799-4e70-95b9-0edc715a2223")

    targets = [
        ("media_1788492613607.jpg", "test_photo_1_jacket_full.png", "test_photo_1_jacket_crop.png"),
        ("media_1788492613729.jpg", "test_photo_2_sideway_full.png", "test_photo_2_sideway_crop.png"),
        ("media_1788492613736.jpg", "test_photo_3_closeup_full.png", "test_photo_3_closeup_crop.png"),
    ]

    for fname, out_name, crop_name in targets:
        t_path = user_upload_dir / fname
        out_path = artifacts_dir / out_name
        crop_path = artifacts_dir / crop_name
        process_image(t_path, source_img, app, swapper, gpen_session, out_path, crop_path)

    print("\n======================================================================")
    print("  [OK] BATCH COMPLETADO CON EXITO PARA LAS 3 FOTOS")
    print("======================================================================")

if __name__ == "__main__":
    main()
