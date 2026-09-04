"""Port interface for Facial Segmentation and Occlusion Mask Parsing."""
from abc import ABC, abstractmethod
import numpy as np


class IFaceParser(ABC):
    """Port for parsing facial regions, hair, glasses, hands, and generating feathered masks."""

    @abstractmethod
    def generate_face_mask(self, image: np.ndarray, feather_radius: int = 5) -> np.ndarray:
        """Generates a continuous float32 face mask [0.0, 1.0] with edge feathering."""
        pass

    @abstractmethod
    def exclude_occlusions(self, base_mask: np.ndarray, image: np.ndarray) -> np.ndarray:
        """Subtracts hair strands, eyewear, and occluding objects from the facial mask."""
        pass
