"""Unit tests for 3D Pose Estimation and Facial Landmark Detection Adapter."""
import pytest
import numpy as np

from src.domain.enums import AngleQuadrant
from src.domain.entities import FaceCrop, HeadPose3D
from src.domain.exceptions import FaceNotFoundException
from src.infrastructure.adapters.pose_estimator_adapter import PoseEstimatorAdapter


class TestPoseEstimatorAdapter:
    def test_sharpness_calculation_sharp_vs_blurry(self):
        adapter = PoseEstimatorAdapter()

        # Sharp synthetic image (checkerboard pattern)
        sharp_img = np.zeros((200, 200, 3), dtype=np.uint8)
        sharp_img[::20, :, :] = 255
        sharp_img[:, ::20, :] = 255

        # Blurry image (uniform flat gray)
        blurry_img = np.ones((200, 200, 3), dtype=np.uint8) * 128

        sharp_score = adapter.calculate_sharpness(sharp_img)
        blurry_score = adapter.calculate_sharpness(blurry_img)

        assert sharp_score > 500.0
        assert blurry_score < 10.0

    def test_estimate_head_pose_frontal_geometry(self):
        adapter = PoseEstimatorAdapter()

        # Standard symmetrical 5 facial landmarks:
        # [left_eye, right_eye, nose_tip, mouth_left, mouth_right]
        # Coordinates in a 112x112 crop
        frontal_landmarks = [
            (38.2946, 51.6963),   # Left eye
            (73.5318, 51.5014),   # Right eye
            (56.0252, 71.7366),   # Nose tip
            (41.5493, 92.3655),   # Mouth left
            (70.7299, 92.2041),   # Mouth right
        ]

        pose = adapter.estimate_head_pose_from_landmarks(frontal_landmarks, image_size=(112, 112))
        assert isinstance(pose, HeadPose3D)
        assert abs(pose.yaw) < 15.0
        assert abs(pose.pitch) < 15.0
        assert pose.quadrant == AngleQuadrant.FRONTAL

    def test_estimate_head_pose_profile_left_geometry(self):
        adapter = PoseEstimatorAdapter()

        # Landmarks compressed horizontally on the left side (facing left / yaw < -45)
        turned_left_landmarks = [
            (25.0, 52.0),
            (50.0, 51.0),
            (28.0, 72.0),
            (28.0, 92.0),
            (48.0, 92.0),
        ]

        pose = adapter.estimate_head_pose_from_landmarks(turned_left_landmarks, image_size=(112, 112))
        assert pose.yaw < -15.0
        assert pose.quadrant in [AngleQuadrant.THREE_QUARTER_LEFT, AngleQuadrant.PROFILE_LEFT]

    def test_estimate_head_pose_profile_right_geometry(self):
        adapter = PoseEstimatorAdapter()

        # Landmarks compressed on right side (facing right / yaw > 15)
        turned_right_landmarks = [
            (62.0, 51.0),
            (87.0, 52.0),
            (84.0, 72.0),
            (64.0, 92.0),
            (84.0, 92.0),
        ]

        pose = adapter.estimate_head_pose_from_landmarks(turned_right_landmarks, image_size=(112, 112))
        assert pose.yaw > 15.0
        assert pose.quadrant in [AngleQuadrant.THREE_QUARTER_RIGHT, AngleQuadrant.PROFILE_RIGHT]

    def test_crop_face_with_low_confidence_raises_exception(self):
        adapter = PoseEstimatorAdapter()
        # Empty black image
        empty_img = np.zeros((100, 100, 3), dtype=np.uint8)

        with pytest.raises(FaceNotFoundException):
            adapter.detect_primary_face(empty_img, min_confidence=0.65)
