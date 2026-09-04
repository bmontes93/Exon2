"""Wavelet Frequency Blending and CIELAB Color Matcher Adapter."""
from typing import Tuple
import numpy as np

from src.application.ports.image_blender import IImageBlender


def _gaussian_blur_2d(channel: np.ndarray, sigma: float = 2.0) -> np.ndarray:
    """Applies Gaussian smoothing on a 2D float array using SciPy or NumPy separable 1D kernels."""
    try:
        from scipy.ndimage import gaussian_filter
        return gaussian_filter(channel, sigma=sigma)
    except ImportError:
        # 1D separable binomial kernel approximation
        kernel_radius = int(max(1, sigma * 2))
        x = np.arange(-kernel_radius, kernel_radius + 1)
        kernel_1d = np.exp(-0.5 * (x / sigma) ** 2)
        kernel_1d /= kernel_1d.sum()

        # Apply along rows then columns
        blurred = np.apply_along_axis(lambda m: np.convolve(m, kernel_1d, mode="same"), axis=1, arr=channel)
        blurred = np.apply_along_axis(lambda m: np.convolve(m, kernel_1d, mode="same"), axis=0, arr=blurred)
        return blurred


def _rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """Converts RGB uint8 to CIE-LAB float32 representation."""
    try:
        import cv2
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    except ImportError:
        # Pure numpy simplified linear color space transformation
        # R, G, B in [0, 1]
        r = rgb[:, :, 0].astype(np.float32) / 255.0
        g = rgb[:, :, 1].astype(np.float32) / 255.0
        b = rgb[:, :, 2].astype(np.float32) / 255.0

        # Approximate L, A, B channels
        l_chan = 0.299 * r + 0.587 * g + 0.114 * b
        a_chan = (r - g) * 0.5 + 0.5
        b_chan = (0.5 * (r + g) - b) * 0.5 + 0.5
        return np.stack([l_chan * 100.0, (a_chan - 0.5) * 200.0, (b_chan - 0.5) * 200.0], axis=-1)


def _lab_to_rgb(lab: np.ndarray) -> np.ndarray:
    """Converts CIE-LAB float32 back to RGB uint8."""
    try:
        import cv2
        lab_uint8 = np.clip(lab, 0, 255).astype(np.uint8)
        return cv2.cvtColor(lab_uint8, cv2.COLOR_LAB2RGB)
    except ImportError:
        l_chan = lab[:, :, 0] / 100.0
        a_chan = lab[:, :, 1] / 200.0
        b_chan = lab[:, :, 2] / 200.0

        r = l_chan + a_chan
        g = l_chan - a_chan * 0.5
        b = l_chan - b_chan

        rgb = np.stack([r, g, b], axis=-1) * 255.0
        return np.clip(rgb, 0, 255).astype(np.uint8)


class WaveletBlenderAdapter(IImageBlender):
    """
    Implements multi-frequency Wavelet / Fourier decomposition and CIELAB color transfer.
    Preserves micro-details (skin pores, film grain, wrinkles) and matches tonal distributions.
    """

    def match_color_cielab(
        self, source_rgb: np.ndarray, target_rgb: np.ndarray
    ) -> np.ndarray:
        """Transfers the mean and standard deviation color distribution from target to source."""
        if source_rgb is None or target_rgb is None:
            return source_rgb

        src_lab = _rgb_to_lab(source_rgb)
        tgt_lab = _rgb_to_lab(target_rgb)

        matched_lab = np.zeros_like(src_lab)

        for c in range(3):
            src_mean, src_std = np.mean(src_lab[:, :, c]), np.std(src_lab[:, :, c])
            tgt_mean, tgt_std = np.mean(tgt_lab[:, :, c]), np.std(tgt_lab[:, :, c])

            src_std = max(1e-4, src_std)
            # Reinhard color transfer formulation
            scale = tgt_std / src_std
            matched_lab[:, :, c] = (src_lab[:, :, c] - src_mean) * scale + tgt_mean

        return _lab_to_rgb(matched_lab)

    def decompose_frequencies(
        self, image: np.ndarray, sigma: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Decomposes an RGB image into:
        - Low Frequency: Smooth macro structure and lighting
        - High Frequency: Residual micro texture, grain, and sharp edges
        """
        img_float = image.astype(np.float32)
        low_freq = np.zeros_like(img_float)

        for c in range(3):
            low_freq[:, :, c] = _gaussian_blur_2d(img_float[:, :, c], sigma=sigma)

        high_freq = img_float - low_freq
        return np.clip(low_freq, 0, 255).astype(np.uint8), high_freq

    def blend_frequencies(
        self,
        synthesized_rgb: np.ndarray,
        original_target_rgb: np.ndarray,
        mask: np.ndarray,
        high_pass_gain: float = 1.0,
    ) -> np.ndarray:
        """
        Blends low frequencies of synthesized face with high frequencies of original target.
        Applies high-pass gain slider for adjustable texture sharpness.
        """
        # Ensure mask is broadcastable [H, W, 1]
        if len(mask.shape) == 2:
            mask_3d = np.expand_dims(mask.astype(np.float32), axis=-1)
        else:
            mask_3d = mask.astype(np.float32)

        # 1. Color match the synthesized face to target tone
        color_matched_synth = self.match_color_cielab(synthesized_rgb, original_target_rgb)

        # 2. Decompose both images
        low_synth, high_synth = self.decompose_frequencies(color_matched_synth, sigma=2.5)
        low_orig, high_orig = self.decompose_frequencies(original_target_rgb, sigma=2.5)

        # 3. Blend Low Frequencies (Smooth transition of identity)
        blended_low = (1.0 - mask_3d) * low_orig.astype(np.float32) + mask_3d * low_synth.astype(np.float32)

        # 4. Blend High Frequencies (Retain original skin grain / pores on top of identity)
        target_high_boosted = high_orig * high_pass_gain
        blended_high = (1.0 - mask_3d) * high_orig + mask_3d * target_high_boosted

        # 5. Composite back
        final_composite = np.clip(blended_low + blended_high, 0, 255).astype(np.uint8)
        return final_composite
