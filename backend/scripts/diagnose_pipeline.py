"""Deep diagnostic script for EXON-FACE neural pipeline."""
import sys
from pathlib import Path
import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from insightface.model_zoo import get_model

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.infrastructure.storage.sqlite_metadata_repo import SQLiteMetadataRepo

def main():
    print("=" * 80)
    print("  EXON-FACE — DIAGNÓSTICO PROFUNDO DE INFERENCIA NEURAL Y SWAP")
    print("=" * 80)

    # 1. Inspect SQLite Database
    repo = SQLiteMetadataRepo("exon_metadata.db")
    profile = repo.get_subject_profile("julio")
    print(f"[*] Sujeto en DB: {profile.name if profile else 'NO ENCONTRADO'}")
    if not profile:
        print("[!] ERROR: Sujeto 'julio' no existe en exon_metadata.db")
        return

    stored_emb = np.array(list(profile.embeddings_by_quadrant.values())[0], dtype=np.float32)
    print(f"[*] Embedding en DB: shape={stored_emb.shape}, norm={np.linalg.norm(stored_emb):.4f}, mean={np.mean(stored_emb):.6f}, min={np.min(stored_emb):.4f}, max={np.max(stored_emb):.4f}")

    # 2. Initialize Models
    print("\n[*] Cargando FaceAnalysis (SCRFD + ArcFace w600k)...")
    analyser = FaceAnalysis(name="buffalo_l", root=r"D:\EXON2\models", providers=["CPUExecutionProvider"])
    analyser.prepare(ctx_id=0, det_size=(640, 640))

    print("[*] Cargando InSwapper ONNX...")
    swapper = get_model(r"D:\EXON2\models\swappers\inswapper_128.onnx", providers=["CPUExecutionProvider"])

    print("[*] Cargando GPEN Enhancer ONNX...")
    import onnxruntime as ort
    gpen_session = ort.InferenceSession(r"D:\EXON2\models\codeformer\GPEN-BFR-512.onnx", providers=["CPUExecutionProvider"])

    # 3. Load a real Julio photo as source
    julio_path = Path(r"Z:\MASIEL FOTOS\julio\IMG_0020.JPG")
    print(f"\n[*] Leyendo foto fuente de Julio: {julio_path}")
    julio_img = cv2.imread(str(julio_path))
    if julio_img is None:
        print(f"[!] Error: No se pudo leer {julio_path}")
        return

    julio_faces = analyser.get(julio_img)
    print(f"[*] Caras detectadas en foto de Julio: {len(julio_faces)}")
    if not julio_faces:
        print("[!] No se detectó cara en foto de Julio.")
        return

    real_source_face = julio_faces[0]
    fresh_emb = real_source_face.normed_embedding
    print(f"[*] Fresh Embedding de Julio: norm={np.linalg.norm(fresh_emb):.4f}")

    # Cosine similarity between DB embedding and fresh photo embedding
    sim = np.dot(stored_emb, fresh_emb) / (np.linalg.norm(stored_emb) * np.linalg.norm(fresh_emb))
    print(f"[*] Similitud Coseno entre DB y Foto Fresh: {sim:.4f}")

    # 4. Load a target photo (or another photo with a face)
    target_path = Path(r"Z:\MASIEL FOTOS\julio\IMG_0025.JPG")
    print(f"\n[*] Leyendo foto destino: {target_path}")
    target_img = cv2.imread(str(target_path))
    target_faces = analyser.get(target_img)
    print(f"[*] Caras detectadas en foto destino: {len(target_faces)}")
    if not target_faces:
        print("[!] No se detectó cara en foto destino.")
        return

    target_face = target_faces[0]

    # 5. TEST 1: Swap using real_source_face directly
    print("\n[*] EJECUTANDO TEST 1: InSwapper con real_source_face...")
    swapped_1 = swapper.get(target_img.copy(), target_face, real_source_face, paste_back=True)
    diff_1 = np.mean(np.abs(swapped_1.astype(float) - target_img.astype(float)))
    print(f"    -> Diferencia media de píxeles (MAE): {diff_1:.4f}")
    cv2.imwrite("debug_swap_direct.png", swapped_1)
    print("    -> Guardado debug_swap_direct.png")

    # 6. TEST 2: Swap using MockFace with stored DB embedding
    print("\n[*] EJECUTANDO TEST 2: InSwapper con MockFace y stored_emb...")
    class MockFace:
        def __init__(self, emb, kps=None, bbox=None):
            self.normed_embedding = np.array(emb, dtype=np.float32)
            if kps is not None:
                self.kps = np.array(kps, dtype=np.float32)
            if bbox is not None:
                self.bbox = np.array(bbox, dtype=np.float32)

    mock_source = MockFace(stored_emb)
    swapped_2 = swapper.get(target_img.copy(), target_face, mock_source, paste_back=True)
    diff_2 = np.mean(np.abs(swapped_2.astype(float) - target_img.astype(float)))
    print(f"    -> Diferencia media de píxeles (MAE): {diff_2:.4f}")
    cv2.imwrite("debug_swap_mock.png", swapped_2)
    print("    -> Guardado debug_swap_mock.png")

    # 7. Check InSwapper weights / inputs / latent
    print("\n[*] InSwapper Model info:")
    for inp in swapper.session.get_inputs():
        print(f"    Input: {inp.name}, shape={inp.shape}, type={inp.type}")
    for out in swapper.session.get_outputs():
        print(f"    Output: {out.name}, shape={out.shape}, type={out.type}")

    # Check emap (latent embedding mapping matrix in inswapper)
    if hasattr(swapper, "emap"):
        print(f"    InSwapper emap shape: {swapper.emap.shape}")

    print("=" * 80)
    print("  DIAGNÓSTICO COMPLETADO")
    print("=" * 80)

if __name__ == "__main__":
    main()
