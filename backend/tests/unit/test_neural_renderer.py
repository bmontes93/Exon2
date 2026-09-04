"""Unit tests for the Diffusers / Neural Face Synthesis Renderer Adapter."""
import pytest
import numpy as np

from src.domain.entities import HeadPose3D
from src.domain.exceptions import DomainValidationError
from src.infrastructure.adapters.diffusers_renderer import DiffusersRendererAdapter


class TestDiffusersRendererAdapter:
    def test_render_face_swap_standard_output(self):
        renderer = DiffusersRendererAdapter()
        target_crop = np.random.randint(50, 200, (128, 128, 3), dtype=np.uint8)
        identity_emb = [0.1] * 512
        pose = HeadPose3D(yaw=10.0, pitch=5.0, roll=0.0)

        rendered = renderer.render_face_swap(
            target_crop=target_crop,
            identity_embedding=identity_emb,
            target_pose=pose,
            identity_weight=1.0,
        )

        assert isinstance(rendered, np.ndarray)
        assert rendered.shape == target_crop.shape
        assert rendered.dtype == np.uint8

    def test_render_face_swap_invalid_embedding_raises_error(self):
        renderer = DiffusersRendererAdapter()
        target_crop = np.zeros((64, 64, 3), dtype=np.uint8)
        invalid_emb = [0.1] * 128  # Must be 512-dim

        with pytest.raises(DomainValidationError):
            renderer.render_face_swap(
                target_crop=target_crop,
                identity_embedding=invalid_emb,
                target_pose=HeadPose3D(yaw=0.0, pitch=0.0, roll=0.0),
                identity_weight=1.0,
            )

    def test_identity_weight_effect_on_synthesis(self):
        renderer = DiffusersRendererAdapter()
        target_crop = np.ones((64, 64, 3), dtype=np.uint8) * 100
        identity_emb = [1.0] + [0.0] * 511
        pose = HeadPose3D(yaw=0.0, pitch=0.0, roll=0.0)

        out_w0 = renderer.render_face_swap(
            target_crop=target_crop,
            identity_embedding=identity_emb,
            target_pose=pose,
            identity_weight=0.0,
        )

        out_w1 = renderer.render_face_swap(
            target_crop=target_crop,
            identity_embedding=identity_emb,
            target_pose=pose,
            identity_weight=1.5,
        )

        # Output with weight 0 should be identical/closer to target crop than weight 1.5
        diff_0 = np.mean(np.abs(out_w0.astype(np.float32) - target_crop.astype(np.float32)))
        diff_1 = np.mean(np.abs(out_w1.astype(np.float32) - target_crop.astype(np.float32)))
        assert diff_0 <= diff_1
