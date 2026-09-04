"""Integration test suite for FastAPI REST and SSE endpoints."""
import io
import pytest
from fastapi.testclient import TestClient

from src.interfaces.api.app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(
        models_dir=str(tmp_path / "models"),
        datasets_dir=str(tmp_path / "datasets"),
        outputs_dir=str(tmp_path / "outputs"),
        db_path=str(tmp_path / "test_api.db"),
    )
    return TestClient(app)


class TestSystemEndpoints:
    def test_get_system_status(self, client):
        response = client.get("/api/v1/system/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ONLINE"
        assert "vram" in data
        assert "disk" in data

    def test_update_system_paths(self, client, tmp_path):
        new_outputs = str(tmp_path / "new_outputs")
        payload = {"outputs_dir": new_outputs}
        response = client.post("/api/v1/system/config/paths", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["outputs_dir"] == new_outputs


class TestDatasetEndpoints:
    def test_ingest_dataset_and_list_subjects(self, client):
        # Fake valid PNG content
        dummy_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 2000

        files = [
            ("images", ("face1.png", io.BytesIO(dummy_png), "image/png")),
            ("images", ("face2.png", io.BytesIO(dummy_png), "image/png")),
        ]
        data = {
            "subject_id": "subj_api_test",
            "name": "Alex Mercer",
            "min_sharpness": "5.0",
        }

        response = client.post("/api/v1/dataset/ingest", data=data, files=files)
        assert response.status_code == 200
        result = response.json()
        assert result["subject_id"] == "subj_api_test"
        assert result["valid_faces_count"] >= 1

        # Check list subjects
        list_resp = client.get("/api/v1/dataset/subjects")
        assert list_resp.status_code == 200
        subjects = list_resp.json()
        assert any(s["subject_id"] == "subj_api_test" for s in subjects)


class TestRenderEndpoints:
    def test_render_execute_and_query_status(self, client):
        # First ingest a subject
        dummy_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 2000
        files = [("images", ("face1.png", io.BytesIO(dummy_png), "image/png"))]
        client.post(
            "/api/v1/dataset/ingest",
            data={"subject_id": "subj_render_1", "name": "Subject 1", "min_sharpness": "1.0"},
            files=files,
        )

        # Trigger Render
        render_files = {"target_image": ("target.png", io.BytesIO(dummy_png), "image/png")}
        render_data = {
            "subject_id": "subj_render_1",
            "mode": "EXPRESS",
            "identity_weight": "1.0",
            "wavelet_high_pass": "1.0",
            "codeformer_fidelity": "0.75",
            "occlusion_masking": "true",
        }

        exec_resp = client.post("/api/v1/render/execute", data=render_data, files=render_files)
        assert exec_resp.status_code in [200, 202]
        job_data = exec_resp.json()
        assert "job_id" in job_data
        job_id = job_data["job_id"]

        # Check status
        status_resp = client.get(f"/api/v1/render/job/{job_id}")
        assert status_resp.status_code == 200
        assert status_resp.json()["job_id"] == job_id
