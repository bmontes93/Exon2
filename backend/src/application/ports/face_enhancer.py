"""Port interface for Facial Restoration and Super-Resolution."""
from abc import ABC, abstractmethod
import numpy as np


class IFaceEnhancer(ABC):
    """Port for CodeFormer/GPEN facial texture enhancement and artifact removal."""

    @abstractmethod
    def enhance_face(self, image: np.ndarray, fidelity: float = 0.75) -> np.ndarray:
        """
        Enhances face crop with adjustable fidelity ratio:
        1.0 = Maximum identity preservation.
        0.0 = Maximum AI restoration / smoothing.
        """
        pass
