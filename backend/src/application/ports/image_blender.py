"""Port interface for Image Blending, Wavelet Frequency Decomposition, and Color Matching."""
from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np


class IImageBlender(ABC):
    """Port for frequency domain blending, skin texture preservation, and color transfer."""

    @abstractmethod
    def match_color_cielab(
        self, source_rgb: np.ndarray, target_rgb: np.ndarray
    ) -> np.ndarray:
        """Matches the color histogram of the source image to target in CIELAB space."""
        pass

    @abstractmethod
    def decompose_frequencies(
        self, image: np.ndarray, sigma: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Decomposes an image into Low Frequency (structure) and High Frequency (texture/grain)."""
        pass

    @abstractmethod
    def blend_frequencies(
        self,
        synthesized_rgb: np.ndarray,
        original_target_rgb: np.ndarray,
        mask: np.ndarray,
        high_pass_gain: float = 1.0,
    ) -> np.ndarray:
        """
        Blends the synthesized face into the target image using frequency separation,
        preserving original skin texture, film grain, and pores.
        """
        pass
