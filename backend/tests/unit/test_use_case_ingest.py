"""Unit tests for IngestSubjectDatasetUseCase."""
import pytest
import numpy as np

from src.domain.enums import AngleQuadrant
from src.infrastructure.adapters.pose_estimator_adapter import PoseEstimatorAdapter
from src.infrastructure.adapters.insightface_adapter import InsightFaceAdapter
from src.infrastructure.storage.local_storage_adapter import LocalStorageAdapter
from src.infrastructure.storage.sqlite_metadata_repo import SQLiteMetadataRepo
from src.application.use_cases.ingest_subject_dataset import (
    IngestSubjectDatasetUseCase,
    IngestInputImage,
)


class TestIngestSubjectDatasetUseCase:
    def test_successful_ingestion_and_profile_cataloging(self, tmp_path):
        storage = LocalStorageAdapter(
            models_dir=tmp_path / "models",
            datasets_dir=tmp_path / "datasets",
            outputs_dir=tmp_path / "outputs",
        )
        repo = SQLiteMetadataRepo(db_path=tmp_path / "metadata.db")
        detector = PoseEstimatorAdapter()
        embedder = InsightFaceAdapter()

        use_case = IngestSubjectDatasetUseCase(
            storage_adapter=storage,
            metadata_repo=repo,
            face_detector=detector,
            identity_extractor=embedder,
        )

        # Create 2 synthetic valid images (PNG format with high contrast)
        np.random.seed(42)
        valid_img = np.random.randint(50, 200, (120, 120, 3), dtype=np.uint8)
        # Encode as fake PNG with magic header
        valid_bytes = b"\x89PNG\r\n\x1a\n" + valid_img.tobytes()

        images = [
            IngestInputImage(filename="face_front.png", raw_bytes=valid_bytes, image_np=valid_img),
            IngestInputImage(filename="face_front2.png", raw_bytes=valid_bytes, image_np=valid_img),
        ]

        result = use_case.execute(
            subject_id="subj_001",
            name="John Doe",
            images=images,
            min_sharpness=5.0,
        )

        assert result.subject_id == "subj_001"
        assert result.name == "John Doe"
        assert result.processed_count == 2
        assert result.valid_faces_count == 2
        assert result.discarded_count == 0
        assert len(result.quadrants_covered) >= 1

        # Verify persisted profile in SQLite
        saved_profile = repo.get_subject_profile("subj_001")
        assert saved_profile is not None
        assert saved_profile.name == "John Doe"
        assert len(saved_profile.embeddings_by_quadrant) >= 1
