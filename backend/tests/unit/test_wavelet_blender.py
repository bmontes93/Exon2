"""Unit tests for Wavelet Frequency Blending and CIELAB Color Matcher Adapter."""
import pytest
import numpy as np

from src.infrastructure.adapters.wavelet_blender import WaveletBlenderAdapter


class TestWaveletBlenderAdapter:
    def test_cielab_color_transfer(self):
        blender = WaveletBlenderAdapter()

        # Source image (e.g. reddish tone)
        src = np.zeros((100, 100, 3), dtype=np.uint8)
        src[:, :, 0] = 200  # Red dominant

        # Target image (e.g. bluish tone)
        target = np.zeros((100, 100, 3), dtype=np.uint8)
        target[:, :, 2] = 180  # Blue dominant

        matched = blender.match_color_cielab(source_rgb=src, target_rgb=target)

        assert matched.shape == src.shape
        assert matched.dtype == np.uint8
        # The matched image should now have higher blue component than original red
        assert np.mean(matched[:, :, 2]) > np.mean(matched[:, :, 0])

    def test_frequency_decomposition_and_reconstruction(self):
        blender = WaveletBlenderAdapter()

        # Synthetic image with smooth gradients + sharp high frequency noise
        base = np.linspace(50, 200, 128, dtype=np.float32).reshape(1, 128)
        base = np.repeat(base, 128, axis=0)
        img = np.stack([base, base, base], axis=-1).astype(np.uint8)

        low_freq, high_freq = blender.decompose_frequencies(img, sigma=2.0)

        assert low_freq.shape == img.shape
        assert high_freq.shape == img.shape

        # Reconstructed sum should closely match original
        reconstructed = np.clip(low_freq.astype(np.float32) + high_freq.astype(np.float32), 0, 255).astype(np.uint8)
        diff = np.abs(img.astype(np.int32) - reconstructed.astype(np.int32))
        assert np.mean(diff) < 2.0

    def test_wavelet_blend_with_high_pass_gain(self):
        blender = WaveletBlenderAdapter()

        target_grainy = np.random.randint(100, 150, (64, 64, 3), dtype=np.uint8)
        synth_smooth = np.ones((64, 64, 3), dtype=np.uint8) * 120
        mask = np.ones((64, 64), dtype=np.float32)  # Full face mask

        # Blend with 1.5x high-pass texture retention
        blended = blender.blend_frequencies(
            synthesized_rgb=synth_smooth,
            original_target_rgb=target_grainy,
            mask=mask,
            high_pass_gain=1.5,
        )

        assert blended.shape == (64, 64, 3)
        assert blended.dtype == np.uint8
        # Ensure high frequency detail from target is present in output
        assert np.std(blended) > 0.0
