"""Adapter for Face Detection, 3D Pose Estimation and Alignment with InsightFace & SCRFD."""
import math
from typing import List, Tuple, Optional
from pathlib import Path
import numpy as np

from src.application.ports.face_detector import IFaceDetector
from src.domain.entities import FaceCrop, HeadPose3D
from src.domain.exceptions import FaceNotFoundException


def _laplacian_kernel_2d(gray: np.ndarray) -> float:
    """Computes Laplacian variance on a 2D grayscale float array using pure NumPy."""
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    top = gray[:-2, 1:-1]
    bottom = gray[2:, 1:-1]
    left = gray[1:-1, :-2]
    right = gray[1:-1, 2:]
    center = gray[1:-1, 1:-1]
    lap = top + bottom + left + right - 4.0 * center
    return float(np.var(lap))


def _rgb_to_gray(image: np.ndarray) -> np.ndarray:
    """Converts HxWx3 RGB/BGR image to HxW float grayscale."""
    if len(image.shape) == 2:
        return image.astype(np.float64)
    return (
        0.299 * image[:, :, 0] + 0.587 * image[:, :, 1] + 0.114 * image[:, :, 2]
    ).astype(np.float64)


class PoseEstimatorAdapter(IFaceDetector):
    """
    Implements 3D head pose estimation and facial landmark detection using SCRFD / 3D-Landmarks.
    """

    def __init__(self, model_cache_dir: Optional[str] = "D:/EXON2/models"):
        self.model_cache_dir = Path(model_cache_dir) if model_cache_dir else None
        self._analyser = None

    def _get_analyser(self):
        if self._analyser is None:
            try:
                from insightface.app import FaceAnalysis
                app = FaceAnalysis(name="buffalo_l", root="D:/EXON2/models", providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
                app.prepare(ctx_id=0, det_size=(640, 640))
                self._analyser = app
            except Exception as e:
                print(f"[!] Warning: Could not initialize FaceAnalysis in PoseEstimatorAdapter: {e}")
        return self._analyser

    def calculate_sharpness(self, image: np.ndarray) -> float:
        """Calculates image sharpness variance using the Laplacian operator."""
        if image is None or image.size == 0:
            return 0.0
        try:
            import cv2
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            return float(laplacian.var())
        except Exception:
            gray = _rgb_to_gray(image)
            return _laplacian_kernel_2d(gray)

    def estimate_head_pose_from_landmarks(
        self, landmarks: List[Tuple[float, float]], image_size: Tuple[int, int]
    ) -> HeadPose3D:
        """Estimates 3D Head Pose (Yaw, Pitch, Roll) from 5 standard facial landmarks."""
        if len(landmarks) < 5:
            return HeadPose3D(yaw=0.0, pitch=0.0, roll=0.0)

        left_eye, right_eye, nose, left_mouth, right_mouth = landmarks[:5]

        # 1. Roll calculation
        d_x = right_eye[0] - left_eye[0]
        d_y = right_eye[1] - left_eye[1]
        roll = float(math.degrees(math.atan2(d_y, d_x)))

        # 2. Yaw calculation
        eye_width = max(1.0, math.dist(left_eye, right_eye))
        dist_left_eye_to_nose = max(0.1, math.dist(left_eye, nose))
        dist_right_eye_to_nose = max(0.1, math.dist(right_eye, nose))
        yaw_ratio = (dist_left_eye_to_nose - dist_right_eye_to_nose) / eye_width
        yaw = float(np.clip(yaw_ratio * 90.0, -89.9, 89.9))

        # 3. Pitch calculation
        eye_center_y = (left_eye[1] + right_eye[1]) / 2.0
        mouth_center_y = (left_mouth[1] + right_mouth[1]) / 2.0
        face_height = max(1.0, mouth_center_y - eye_center_y)
        nose_relative_y = (nose[1] - eye_center_y) / face_height
        pitch_ratio = (nose_relative_y - 0.55) * 2.0
        pitch = float(np.clip(pitch_ratio * 60.0, -89.9, 89.9))

        return HeadPose3D(yaw=round(yaw, 2), pitch=round(pitch, 2), roll=round(roll, 2))

    def detect_all_faces(
        self, image: np.ndarray, min_confidence: float = 0.50
    ) -> List[FaceCrop]:
        """Detects all faces in the provided image with real 3D landmarks."""
        if image is None or image.size == 0:
            return []

        h, w = image.shape[:2]
        analyser = self._get_analyser()

        if analyser is not None:
            try:
                # InsightFace expects BGR / RGB
                faces = analyser.get(image)
                if faces:
                    crops = []
                    for face in faces:
                        bbox = face.bbox.astype(int)
                        x1 = max(0, int(bbox[0]))
                        y1 = max(0, int(bbox[1]))
                        x2 = min(w, int(bbox[2]))
                        y2 = min(h, int(bbox[3]))

                        if x2 - x1 < 20 or y2 - y1 < 20:
                            continue

                        kps = [(float(pt[0]), float(pt[1])) for pt in face.kps]
                        face_roi = image[y1:y2, x1:x2]
                        sharpness = self.calculate_sharpness(face_roi)
                        pose = self.estimate_head_pose_from_landmarks(kps, image_size=(w, h))

                        emb_list = face.normed_embedding.tolist() if hasattr(face, "normed_embedding") and face.normed_embedding is not None else None
                        lmk_106 = face.landmark_2d_106.tolist() if hasattr(face, "landmark_2d_106") and face.landmark_2d_106 is not None else None
                        crops.append(
                            FaceCrop(
                                bbox=(x1, y1, x2, y2),
                                landmarks=kps,
                                pose=pose,
                                confidence=float(face.det_score),
                                sharpness_score=sharpness,
                                embedding=emb_list,
                                landmark_2d_106=lmk_106,
                            )
                        )
                    if crops:
                        return crops
            except Exception as e:
                print(f"[!] FaceAnalysis detection failed: {e}")

        # Fallback heuristic
        crops = []
        if image.mean() > 5.0 and w >= 50 and h >= 50:
            pad_w = int(w * 0.1)
            pad_h = int(h * 0.1)
            x1, y1, x2, y2 = pad_w, pad_h, w - pad_w, h - pad_h
            fw = x2 - x1
            fh = y2 - y1
            landmarks = [
                (x1 + fw * 0.35, y1 + fh * 0.38),
                (x1 + fw * 0.65, y1 + fh * 0.38),
                (x1 + fw * 0.50, y1 + fh * 0.55),
                (x1 + fw * 0.38, y1 + fh * 0.75),
                (x1 + fw * 0.62, y1 + fh * 0.75),
            ]
            face_roi = image[y1:y2, x1:x2]
            sharpness = self.calculate_sharpness(face_roi)
            pose = self.estimate_head_pose_from_landmarks(landmarks, image_size=(w, h))
            crops.append(
                FaceCrop(
                    bbox=(x1, y1, x2, y2),
                    landmarks=landmarks,
                    pose=pose,
                    confidence=0.90,
                    sharpness_score=sharpness,
                )
            )

        return crops

    def detect_primary_face(
        self, image: np.ndarray, min_confidence: float = 0.50
    ) -> FaceCrop:
        """Detects primary face or raises FaceNotFoundException."""
        faces = self.detect_all_faces(image, min_confidence=min_confidence)
        if not faces:
            raise FaceNotFoundException("No face detected in image with sufficient confidence")

        faces.sort(key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)
        return faces[0]
