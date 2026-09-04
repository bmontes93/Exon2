import cv2
import os
import sys
from pathlib import Path
import numpy as np
from datetime import datetime

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.domain.enums import AngleQuadrant
from src.domain.entities import IdentityProfile
from src.infrastructure.storage.sqlite_metadata_repo import SQLiteMetadataRepo
from insightface.app import FaceAnalysis

def classify_quadrant(yaw: float, pitch: float) -> AngleQuadrant:
    if pitch > 15.0:
        return AngleQuadrant.PITCH_UP
    elif pitch < -15.0:
        return AngleQuadrant.PITCH_DOWN
    elif yaw < -45.0:
        return AngleQuadrant.PROFILE_LEFT
    elif yaw > 45.0:
        return AngleQuadrant.PROFILE_RIGHT
    elif -45.0 <= yaw < -15.0:
        return AngleQuadrant.THREE_QUARTER_LEFT
    elif 15.0 < yaw <= 45.0:
        return AngleQuadrant.THREE_QUARTER_RIGHT
    else:
        return AngleQuadrant.FRONTAL

def main():
    print("=" * 80)
    print("  CONSTRUCCION DE PERFIL 3D CURADO Y MULTI-ANGULO DE MASIEL")
    print("=" * 80)

    app = FaceAnalysis(name="buffalo_l", root="D:/EXON2/models", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))

    # Sources: Curated video frames + Top photos
    frames_dir = Path("d:/EXON2/backend/curated_frames")
    photo_dir = Path(r"Z:\MASIEL FOTOS\julio")

    all_image_paths = list(frames_dir.glob("*.jpg"))
    all_image_paths += list(photo_dir.glob("IMG_00*.JPG"))
    all_image_paths += list(photo_dir.glob("rasiel (*).JPG"))[:50]
    print(f"[*] Total de imagenes candidatas para curar: {len(all_image_paths)}")

    quadrant_embeddings = {q: [] for q in AngleQuadrant}
    quadrant_weights = {q: [] for q in AngleQuadrant}

    processed_count = 0
    for img_p in all_image_paths:
        img = cv2.imread(str(img_p))
        if img is None:
            continue

        faces = app.get(img)
        if not faces:
            continue

        face = faces[0]
        if face.det_score < 0.70:
            continue

        pitch = float(face.pose[0]) if hasattr(face, "pose") else 0.0
        yaw = float(face.pose[1]) if hasattr(face, "pose") else 0.0

        quadrant = classify_quadrant(yaw, pitch)
        emb = face.normed_embedding

        # Weight by detection score and face size
        bx1, by1, bx2, by2 = face.bbox.astype(int)
        area = max(1, (bx2 - bx1) * (by2 - by1))
        weight = float(face.det_score) * np.sqrt(area)

        quadrant_embeddings[quadrant].append(emb)
        quadrant_weights[quadrant].append(weight)
        processed_count += 1

    print(f"\n[*] Caras analizadas y aceptadas: {processed_count}")
    final_quadrant_map = {}

    for q in AngleQuadrant:
        embs = quadrant_embeddings[q]
        weights = quadrant_weights[q]
        count = len(embs)
        if count > 0:
            weights_arr = np.array(weights, dtype=np.float32)
            weights_arr /= np.sum(weights_arr)
            # Weighted average
            centroid = np.sum([e * w for e, w in zip(embs, weights_arr)], axis=0)
            norm = np.linalg.norm(centroid)
            if norm > 0:
                centroid /= norm
            final_quadrant_map[q] = centroid.tolist()
            print(f"    -> Cuadrante {q.value:20s}: {count:3d} muestras integradas (norma=1.0)")
        else:
            print(f"    -> Cuadrante {q.value:20s}: 0 muestras directas")

    # If any quadrant is missing, fallback to FRONTAL
    if AngleQuadrant.FRONTAL in final_quadrant_map:
        base_emb = final_quadrant_map[AngleQuadrant.FRONTAL]
        for q in AngleQuadrant:
            if q not in final_quadrant_map:
                final_quadrant_map[q] = base_emb
                print(f"    [!] Cuadrante {q.value} suplido con FRONTAL")

    # Save to SQLite
    repo = SQLiteMetadataRepo("backend/exon_metadata.db")
    profile = IdentityProfile(
        subject_id="julio",
        name="Masiel",
        embeddings_by_quadrant=final_quadrant_map,
        created_at=datetime.utcnow(),
    )
    repo.save_subject_profile(profile)
    print("\n[OK] Perfil 'julio' (Masiel) guardado exitosamente en backend/exon_metadata.db")

if __name__ == "__main__":
    main()
