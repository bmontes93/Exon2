"""Unit tests for Local Storage Adapter and SQLite Metadata Repository."""
import pytest
from pathlib import Path

from src.domain.entities import IdentityProfile, RenderJob, RenderParams
from src.domain.enums import AngleQuadrant, RenderMode, JobStatus
from src.infrastructure.storage.local_storage_adapter import LocalStorageAdapter
from src.infrastructure.storage.sqlite_metadata_repo import SQLiteMetadataRepo


class TestLocalStorageAdapter:
    def test_initialization_creates_directories(self, tmp_path):
        adapter = LocalStorageAdapter(
            models_dir=tmp_path / "models",
            datasets_dir=tmp_path / "datasets",
            outputs_dir=tmp_path / "outputs",
        )
        assert adapter.models_dir.exists()
        assert adapter.datasets_dir.exists()
        assert adapter.outputs_dir.exists()

    def test_save_and_retrieve_file(self, tmp_path):
        adapter = LocalStorageAdapter(
            models_dir=tmp_path / "models",
            datasets_dir=tmp_path / "datasets",
            outputs_dir=tmp_path / "outputs",
        )
        dummy_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
        saved_path = adapter.save_output_image("test_render.png", dummy_content)
        assert saved_path.exists()
        assert saved_path.read_bytes() == dummy_content

    def test_get_storage_metrics(self, tmp_path):
        adapter = LocalStorageAdapter(
            models_dir=tmp_path / "models",
            datasets_dir=tmp_path / "datasets",
            outputs_dir=tmp_path / "outputs",
        )
        metrics = adapter.get_disk_metrics()
        assert "free_gb" in metrics
        assert "total_gb" in metrics
        assert metrics["free_gb"] > 0


class TestSQLiteMetadataRepo:
    def test_subject_profile_crud(self, tmp_path):
        db_path = tmp_path / "exon_metadata.db"
        repo = SQLiteMetadataRepo(db_path=db_path)

        profile = IdentityProfile(
            subject_id="subj_test_1",
            name="Alice",
            embeddings_by_quadrant={
                AngleQuadrant.FRONTAL: [0.1] * 512,
                AngleQuadrant.PROFILE_LEFT: [0.2] * 512,
            },
        )

        repo.save_subject_profile(profile)

        # Retrieve
        fetched = repo.get_subject_profile("subj_test_1")
        assert fetched is not None
        assert fetched.subject_id == "subj_test_1"
        assert fetched.name == "Alice"
        assert AngleQuadrant.FRONTAL in fetched.embeddings_by_quadrant
        assert len(fetched.embeddings_by_quadrant[AngleQuadrant.FRONTAL]) == 512

        # List all
        all_subjects = repo.list_subject_profiles()
        assert len(all_subjects) == 1
        assert all_subjects[0].subject_id == "subj_test_1"

    def test_render_job_crud(self, tmp_path):
        db_path = tmp_path / "exon_metadata.db"
        repo = SQLiteMetadataRepo(db_path=db_path)

        job = RenderJob(
            job_id="job_001",
            subject_id="subj_test_1",
            target_image_path="/path/to/target.png",
            mode=RenderMode.EXPRESS,
            params=RenderParams(),
        )

        repo.save_render_job(job)

        # Update progress and complete
        job.update_progress("DIFFUSION", 0.6)
        repo.update_render_job(job)

        fetched = repo.get_render_job("job_001")
        assert fetched is not None
        assert fetched.status == JobStatus.RUNNING
        assert fetched.progress == 0.6
