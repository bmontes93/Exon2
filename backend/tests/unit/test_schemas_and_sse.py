"""Unit tests for Pydantic v2 DTO Schemas and SSE Telemetry Manager."""
import asyncio
import pytest
from pydantic import ValidationError

from src.domain.enums import AngleQuadrant, RenderMode, JobStatus
from src.interfaces.schemas.dataset_schemas import (
    SubjectProfileResponse,
    DatasetIngestResponse,
)
from src.interfaces.schemas.render_schemas import (
    RenderExecuteRequest,
    RenderParamsDTO,
    RenderJobResponse,
)
from src.interfaces.schemas.system_schemas import (
    SystemStatusResponse,
    PathConfigUpdateRequest,
)
from src.interfaces.api.sse_manager import SSEManager, TelemetryEvent


class TestSchemasValidation:
    def test_render_execute_request_valid(self):
        req = RenderExecuteRequest(
            subject_id="subj_001",
            mode=RenderMode.STUDIO_PRO,
            params=RenderParamsDTO(
                identity_weight=1.2,
                wavelet_high_pass=1.5,
                codeformer_fidelity=0.8,
                occlusion_masking=True,
                source_quadrant=AngleQuadrant.FRONTAL,
            ),
        )
        assert req.subject_id == "subj_001"
        assert req.params.identity_weight == 1.2

    def test_render_params_out_of_bounds_validation_error(self):
        with pytest.raises(ValidationError):
            RenderParamsDTO(identity_weight=3.5)  # Max allowed is 2.0

        with pytest.raises(ValidationError):
            RenderParamsDTO(codeformer_fidelity=-0.1)  # Min allowed is 0.0

    def test_system_path_config_validation(self):
        req = PathConfigUpdateRequest(
            models_dir="D:/Storage/Models",
            datasets_dir="D:/Storage/Datasets",
            outputs_dir="D:/Storage/Outputs",
        )
        assert req.models_dir == "D:/Storage/Models"


class TestSSEManager:
    def test_sse_subscribe_and_publish_stream(self):
        async def run_test():
            sse_manager = SSEManager()
            job_id = "job_sse_test_1"

            queue = await sse_manager.subscribe(job_id)

            # Publish event
            await sse_manager.publish(
                job_id,
                TelemetryEvent(
                    step_name="3D_DETECTION",
                    progress=0.25,
                    vram_allocated_mb=1200.0,
                    message="Calculating 3D Pose",
                ),
            )

            # Receive from queue
            event = await asyncio.wait_for(queue.get(), timeout=1.0)
            assert event.step_name == "3D_DETECTION"
            assert event.progress == 0.25
            assert event.vram_allocated_mb == 1200.0

            # Test formatted SSE event line
            sse_line = event.to_sse_format()
            assert sse_line.startswith("data: ")
            assert "3D_DETECTION" in sse_line

            # Unsubscribe
            await sse_manager.unsubscribe(job_id, queue)
            assert len(sse_manager._subscribers.get(job_id, set())) == 0

        asyncio.run(run_test())
