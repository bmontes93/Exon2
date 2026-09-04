"""Abstract port for Face Detection and 3D Pose Estimation."""
from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np

from src.domain.entities import FaceCrop, HeadPose3D


class IFaceDetector(ABC):
    """Port interface for facial detection, 3D pose estimation, and crop alignment."""

    @abstractmethod
    def calculate_sharpness(self, image: np.ndarray) -> float:
        """Calculates image sharpness variance."""
        pass

    @abstractmethod
    def estimate_head_pose_from_landmarks(
        self, landmarks: List[Tuple[float, float]], image_size: Tuple[int, int]
    ) -> HeadPose3D:
        """Estimates 3D Yaw, Pitch, Roll angles from facial landmark coordinates."""
        pass

    @abstractmethod
    def detect_primary_face(
        self, image: np.ndarray, min_confidence: float = 0.65
    ) -> FaceCrop:
        """Detects the most prominent face in the image or raises FaceNotFoundException."""
        pass

    @abstractmethod
    def detect_all_faces(
        self, image: np.ndarray, min_confidence: float = 0.65
    ) -> List[FaceCrop]:
        """Detects all faces in the image."""
        pass
