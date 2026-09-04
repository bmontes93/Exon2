"""End-to-End (E2E) Verification, Security Hardening, and Resilience Suite."""
import io
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from src.interfaces.api.app import create_app


@pytest.fixture
def e2e_environment(tmp_path):
    models_dir = tmp_path / "models"
    datasets_dir = tmp_path / "datasets"
    outputs_dir = tmp_path / "outputs"
    db_path = tmp_path / "e2e_exon.db"

    app = create_app(
        models_dir=str(models_dir),
        datasets_dir=str(datasets_dir),
        outputs_dir=str(outputs_dir),
        db_path=str(db_path),
    )
    client = TestClient(app)
    return {
        "client": client,
        "models_dir": models_dir,
        "datasets_dir": datasets_dir,
        "outputs_dir": outputs_dir,
        "db_path": db_path,
    }


class TestFullPipelineE2E:
    def test_complete_ingest_to_studio_render_lifecycle(self, e2e_environment):
        client = e2e_environment["client"]
        outputs_dir = e2e_environment["outputs_dir"]

        # 1. Ingest Subject Dataset
        dummy_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 3000
        files = [
            ("images", ("front.png", io.BytesIO(dummy_png), "image/png")),
            ("images", ("side_left.png", io.BytesIO(dummy_png), "image/png")),
        ]
        ingest_data = {
            "subject_id": "subj_e2e_hero",
            "name": "Sarah Connor",
            "min_sharpness": "1.0",
        }

        ingest_res = client.post("/api/v1/dataset/ingest", data=ingest_data, files=files)
        assert ingest_res.status_code == 200
        ingest_json = ingest_res.json()
        assert ingest_json["subject_id"] == "subj_e2e_hero"
        assert ingest_json["valid_faces_count"] >= 1

        # 2. Verify Subject is in Catalog
        subjects_res = client.get("/api/v1/dataset/subjects")
        assert subjects_res.status_code == 200
        assert any(s["subject_id"] == "subj_e2e_hero" for s in subjects_res.json())

        # 3. Execute Express Render
        target_file = {"target_image": ("target_crowd.png", io.BytesIO(dummy_png), "image/png")}
        express_data = {
            "subject_id": "subj_e2e_hero",
            "mode": "EXPRESS",
            "identity_weight": "1.0",
            "wavelet_high_pass": "1.0",
            "codeformer_fidelity": "0.75",
            "occlusion_masking": "true",
        }

        render_res = client.post("/api/v1/render/execute", data=express_data, files=target_file)
        assert render_res.status_code in [200, 202]
        job_express = render_res.json()
        assert job_express["status"] == "COMPLETED"
        assert job_express["progress"] == 1.0

        # Verify output file was created on disk
        created_files = list(outputs_dir.glob("*.png"))
        assert len(created_files) >= 1

        # 4. Execute Studio Pro Render with custom weights
        pro_data = {
            "subject_id": "subj_e2e_hero",
            "mode": "STUDIO_PRO",
            "identity_weight": "1.35",
            "wavelet_high_pass": "1.60",
            "codeformer_fidelity": "0.80",
            "occlusion_masking": "true",
            "source_quadrant": "FRONTAL",
        }
        pro_res = client.post("/api/v1/render/execute", data=pro_data, files=target_file)
        assert pro_res.status_code in [200, 202]
        job_pro = pro_res.json()
        assert job_pro["status"] == "COMPLETED"
        assert job_pro["params"]["identity_weight"] == 1.35
        assert job_pro["params"]["wavelet_high_pass"] == 1.60

    def test_security_malicious_payload_rejected(self, e2e_environment):
        client = e2e_environment["client"]

        # Fake executable disguised as PNG
        malicious_bytes = b"MZ\x90\x00" + b"\x00" * 1000
        files = [("images", ("exploit.png", io.BytesIO(malicious_bytes), "image/png"))]
        data = {"subject_id": "subj_hack", "name": "Bad Actor", "min_sharpness": "1.0"}

        res = client.post("/api/v1/dataset/ingest", data=data, files=files)
        # Should be blocked with 403 Forbidden
        assert res.status_code == 403
        assert "SECURITY_VIOLATION" in res.json()["error"]
