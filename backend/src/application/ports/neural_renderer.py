"""Port interface for Neural Generative Face Synthesis."""
from abc import ABC, abstractmethod
from typing import List
import numpy as np

from src.domain.entities import HeadPose3D


class INeuralRenderer(ABC):
    """Port for deep generative identity mapping (SDXL / InstantID / ControlNet)."""

    @abstractmethod
    def render_face_swap(
        self,
        target_crop: np.ndarray,
        identity_embedding: List[float],
        target_pose: HeadPose3D,
        identity_weight: float = 1.0,
    ) -> np.ndarray:
        """Synthesizes target facial crop with source identity conditioning."""
        pass
