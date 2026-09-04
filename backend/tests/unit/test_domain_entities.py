"""Unit tests for Domain Entities, Value Objects, Enums and Domain Exceptions."""
import pytest
import numpy as np

from src.domain.enums import AngleQuadrant, RenderMode, JobStatus
from src.domain.entities import (
    HeadPose3D,
    FaceCrop,
    IdentityProfile,
    RenderJob,
    RenderParams,
)
from src.domain.exceptions import (
    DomainValidationError,
    FaceNotFoundException,
    VRAMExceededException,
    SecurityViolationException,
)


class TestHeadPose3D:
    def test_valid_head_pose_creation(self):
        pose = HeadPose3D(yaw=10.0, pitch=-5.0, roll=2.0)
        assert pose.yaw == 10.0
        assert pose.pitch == -5.0
        assert pose.roll == 2.0

    def test_angle_quadrant_frontal(self):
        pose = HeadPose3D(yaw=5.0, pitch=4.0, roll=0.0)
        assert pose.quadrant == AngleQuadrant.FRONTAL

    def test_angle_quadrant_three_quarter_left(self):
        # Negative yaw = turned to left (or vice versa per convention -15 to -45)
        pose = HeadPose3D(yaw=-30.0, pitch=0.0, roll=0.0)
        assert pose.quadrant == AngleQuadrant.THREE_QUARTER_LEFT

    def test_angle_quadrant_three_quarter_right(self):
        pose = HeadPose3D(yaw=30.0, pitch=0.0, roll=0.0)
        assert pose.quadrant == AngleQuadrant.THREE_QUARTER_RIGHT

    def test_angle_quadrant_profile_left(self):
        pose = HeadPose3D(yaw=-65.0, pitch=0.0, roll=0.0)
        assert pose.quadrant == AngleQuadrant.PROFILE_LEFT

    def test_angle_quadrant_profile_right(self):
        pose = HeadPose3D(yaw=75.0, pitch=0.0, roll=0.0)
        assert pose.quadrant == AngleQuadrant.PROFILE_RIGHT

    def test_invalid_angles_raise_validation_error(self):
        with pytest.raises(DomainValidationError):
            HeadPose3D(yaw=190.0, pitch=0.0, roll=0.0)


class TestFaceCrop:
    def test_face_crop_valid(self):
        bbox = (10, 20, 110, 120)
        landmarks = [(15, 25), (35, 25), (25, 40), (20, 60), (30, 60)]
        pose = HeadPose3D(yaw=0.0, pitch=0.0, roll=0.0)
        crop = FaceCrop(
            bbox=bbox,
            landmarks=landmarks,
            pose=pose,
            confidence=0.98,
            sharpness_score=154.5,
        )
        assert crop.confidence == 0.98
        assert crop.sharpness_score == 154.5
        assert crop.is_sharp(threshold=100.0) is True

    def test_face_crop_invalid_confidence_raises_error(self):
        with pytest.raises(DomainValidationError):
            FaceCrop(
                bbox=(0, 0, 10, 10),
                landmarks=[],
                pose=HeadPose3D(yaw=0.0, pitch=0.0, roll=0.0),
                confidence=1.5,
                sharpness_score=50.0,
            )


class TestIdentityProfile:
    def test_identity_profile_embedding_matching(self):
        # Create normalized 512-dim mock embeddings
        np.random.seed(42)
        v_front = np.random.randn(512)
        v_front /= np.linalg.norm(v_front)

        v_left = np.random.randn(512)
        v_left /= np.linalg.norm(v_left)

        profile = IdentityProfile(
            subject_id="subj_001",
            name="John Doe",
            embeddings_by_quadrant={
                AngleQuadrant.FRONTAL: v_front.tolist(),
                AngleQuadrant.THREE_QUARTER_LEFT: v_left.tolist(),
            },
        )

        best_emb = profile.get_closest_embedding(AngleQuadrant.FRONTAL)
        assert len(best_emb) == 512

        # Fallback to frontal if requested quadrant doesn't exist
        fallback_emb = profile.get_closest_embedding(AngleQuadrant.PROFILE_RIGHT)
        assert fallback_emb == v_front.tolist()


class TestRenderJob:
    def test_render_job_lifecycle_and_params(self):
        params = RenderParams(
            identity_weight=1.2,
            wavelet_high_pass=1.3,
            codeformer_fidelity=0.75,
            occlusion_masking=True,
        )
        job = RenderJob(
            job_id="job_abc123",
            subject_id="subj_001",
            target_image_path="/storage/targets/sample.png",
            mode=RenderMode.STUDIO_PRO,
            params=params,
        )
        assert job.status == JobStatus.PENDING
        assert job.progress == 0.0

        job.update_progress(step_name="3D_DETECTION", progress=0.25)
        assert job.status == JobStatus.RUNNING
        assert job.progress == 0.25
        assert job.current_step == "3D_DETECTION"

        job.complete(output_path="/storage/outputs/result.png")
        assert job.status == JobStatus.COMPLETED
        assert job.progress == 1.0
        assert job.output_path == "/storage/outputs/result.png"

    def test_invalid_render_params_raises_validation_error(self):
        with pytest.raises(DomainValidationError):
            RenderParams(identity_weight=-0.5)  # must be >= 0.0


class TestDomainExceptions:
    def test_exceptions_hierarchy(self):
        assert issubclass(FaceNotFoundException, Exception)
        assert issubclass(VRAMExceededException, Exception)
        assert issubclass(SecurityViolationException, Exception)
