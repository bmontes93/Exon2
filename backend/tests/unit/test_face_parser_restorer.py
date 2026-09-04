"""Unit tests for BiSeNet Occlusion Parser and CodeFormer Face Restorer Adapters."""
import pytest
import numpy as np

from src.infrastructure.adapters.bisenet_parser import BiSeNetParserAdapter
from src.infrastructure.adapters.codeformer_enhancer import CodeFormerEnhancerAdapter


class TestBiSeNetParserAdapter:
    def test_parse_face_mask_dimensions_and_range(self):
        parser = BiSeNetParserAdapter()
        img = np.random.randint(50, 200, (100, 100, 3), dtype=np.uint8)

        mask = parser.generate_face_mask(img, feather_radius=5)

        assert mask.shape == (100, 100)
        assert mask.dtype == np.float32
        assert np.min(mask) >= 0.0
        assert np.max(mask) <= 1.0
        # Center of mask should be closer to 1.0 (face region)
        assert mask[50, 50] > mask[5, 5]

    def test_occlusion_exclusion(self):
        parser = BiSeNetParserAdapter()
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        # Create a bright simulated glasses/hair rectangle across the top
        img[20:30, 20:80, :] = 255

        base_mask = np.ones((100, 100), dtype=np.float32)
        occlusion_mask = parser.exclude_occlusions(base_mask, img)

        assert occlusion_mask.shape == (100, 100)
        # The region with glasses should have reduced mask intensity
        assert np.mean(occlusion_mask[20:30, 20:80]) < np.mean(base_mask[20:30, 20:80])


class TestCodeFormerEnhancerAdapter:
    def test_enhance_face_fidelity_scaling(self):
        enhancer = CodeFormerEnhancerAdapter()
        img = np.random.randint(50, 200, (112, 112, 3), dtype=np.uint8)

        # High fidelity (preserves 80% source identity)
        enhanced_high = enhancer.enhance_face(img, fidelity=0.8)
        # Low fidelity (maximum AI restoration)
        enhanced_low = enhancer.enhance_face(img, fidelity=0.2)

        assert enhanced_high.shape == img.shape
        assert enhanced_low.shape == img.shape
        assert enhanced_high.dtype == np.uint8
        assert enhanced_low.dtype == np.uint8

        # High fidelity output should be closer to original image than low fidelity output
        diff_high = np.mean(np.abs(enhanced_high.astype(np.float32) - img.astype(np.float32)))
        diff_low = np.mean(np.abs(enhanced_low.astype(np.float32) - img.astype(np.float32)))
        assert diff_high <= diff_low
