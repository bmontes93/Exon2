import cv2
import os
import sys
from pathlib import Path
import numpy as np

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from insightface.app import FaceAnalysis

def main():
    out_dir = Path("d:/EXON2/backend/curated_frames")
    out_dir.mkdir(parents=True, exist_ok=True)

    video_dir = Path(r"Z:\MASIEL FOTOS\julio")
    mp4_files = sorted(list(video_dir.glob("*.mp4")))
    print(f"[*] Escaneando {len(mp4_files)} videos...")

    app = FaceAnalysis(name="buffalo_l", root="D:/EXON2/models", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))

    total_extracted = 0

    for v_idx, vpath in enumerate(mp4_files, 1):
        cap = cv2.VideoCapture(str(vpath))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        step = max(1, int(fps * 0.4))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        candidates = []
        f_idx = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if f_idx % step == 0:
                faces = app.get(frame)
                if faces:
                    for face in faces:
                        bx1, by1, bx2, by2 = face.bbox.astype(int)
                        fw = bx2 - bx1
                        fh = by2 - by1
                        if fw >= 150 and fh >= 150 and face.det_score >= 0.75:
                            crop = frame[max(0, by1):min(frame.shape[0], by2), max(0, bx1):min(frame.shape[1], bx2)]
                            if crop.size > 0:
                                gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                                sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                                candidates.append({
                                    "frame": frame.copy(),
                                    "sharpness": sharpness,
                                    "f_idx": f_idx,
                                    "pitch": float(face.pose[0]) if hasattr(face, "pose") else 0.0,
                                    "yaw": float(face.pose[1]) if hasattr(face, "pose") else 0.0,
                                })
            f_idx += 1

        cap.release()

        # Sort and take top 2 sharpest distinct frames
        candidates.sort(key=lambda x: x["sharpness"], reverse=True)
        selected = candidates[:2]

        for k_idx, item in enumerate(selected):
            sh = int(item["sharpness"])
            sname = f"vid_{v_idx:02d}_top{k_idx+1}_sh{sh}.jpg"
            cv2.imwrite(str(out_dir / sname), item["frame"])
            total_extracted += 1
            print(f"[{v_idx}/{len(mp4_files)}] Guardado: {sname} (nitidez={sh}, yaw={item['yaw']:.1f}, pitch={item['pitch']:.1f})")

    print(f"\n[OK] Extraccion finalizada. Total fotogramas extraidos: {total_extracted}")

if __name__ == "__main__":
    main()
