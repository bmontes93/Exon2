"""Face synthesis render execution and telemetry streaming router."""
import uuid
from typing import Optional
import numpy as np
from fastapi import APIRouter, File, Form, UploadFile, Request, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from src.domain.entities import RenderParams
from src.domain.enums import AngleQuadrant, RenderMode, JobStatus
from src.application.use_cases.execute_face_synthesis import ExecuteFaceSynthesisUseCase
from src.interfaces.schemas.render_schemas import (
    RenderJobResponse,
    RenderParamsDTO,
)
from src.interfaces.api.sse_manager import TelemetryEvent

router = APIRouter(prefix="/render", tags=["Render"])


@router.post("/execute", response_model=RenderJobResponse)
async def execute_render(
    request: Request,
    background_tasks: BackgroundTasks,
    subject_id: str = Form(...),
    mode: RenderMode = Form(RenderMode.EXPRESS),
    identity_weight: float = Form(1.0),
    wavelet_high_pass: float = Form(1.0),
    codeformer_fidelity: float = Form(0.75),
    occlusion_masking: bool = Form(True),
    source_quadrant: Optional[str] = Form(None),
    target_image: UploadFile = File(...),
):
    """Initiates an asynchronous face swap render job."""
    container = request.app.state.container
    raw_bytes = await target_image.read()

    try:
        import cv2
        nparr = np.frombuffer(raw_bytes, np.uint8)
        target_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if target_np is None:
            raise ValueError()
    except Exception:
        target_np = np.zeros((150, 150, 3), dtype=np.uint8)
        target_np[::10, :, :] = 255
        target_np[:, ::10, :] = 255

    job_id = f"job_{uuid.uuid4().hex[:10]}"

    parsed_quadrant = AngleQuadrant(source_quadrant) if source_quadrant else None
    params = RenderParams(
        identity_weight=identity_weight,
        wavelet_high_pass=wavelet_high_pass,
        codeformer_fidelity=codeformer_fidelity,
        occlusion_masking=occlusion_masking,
        source_quadrant=parsed_quadrant,
    )

    use_case = ExecuteFaceSynthesisUseCase(
        storage_adapter=container.storage_adapter,
        metadata_repo=container.metadata_repo,
        face_detector=container.face_detector,
        identity_extractor=container.identity_extractor,
        neural_renderer=container.neural_renderer,
        face_parser=container.face_parser,
        image_blender=container.image_blender,
        face_enhancer=container.face_enhancer,
        vram_orchestrator=container.vram_orchestrator,
    )

    async def _progress_callback(step: str, prog: float):
        vram_stats = container.vram_orchestrator.get_vram_stats()
        await container.sse_manager.publish(
            job_id,
            TelemetryEvent(
                step_name=step,
                progress=prog,
                vram_allocated_mb=vram_stats.allocated_mb,
                message=f"Processing {step}",
            ),
        )

    # Execute directly or schedule
    job = await use_case.execute(
        job_id=job_id,
        subject_id=subject_id,
        target_image_np=target_np,
        mode=mode,
        params=params,
        progress_callback=lambda s, p: background_tasks.add_task(_progress_callback, s, p),
    )

    return RenderJobResponse(
        job_id=job.job_id,
        subject_id=job.subject_id,
        target_image_path=job.target_image_path,
        mode=job.mode,
        params=RenderParamsDTO(
            identity_weight=job.params.identity_weight,
            wavelet_high_pass=job.params.wavelet_high_pass,
            codeformer_fidelity=job.params.codeformer_fidelity,
            occlusion_masking=job.params.occlusion_masking,
            source_quadrant=job.params.source_quadrant,
        ),
        status=job.status,
        progress=job.progress,
        current_step=job.current_step,
        output_path=job.output_path,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.get("/job/{job_id}", response_model=RenderJobResponse)
async def get_job_status(job_id: str, request: Request):
    """Queries the current status and output of a render job."""
    container = request.app.state.container
    job = container.metadata_repo.get_render_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    return RenderJobResponse(
        job_id=job.job_id,
        subject_id=job.subject_id,
        target_image_path=job.target_image_path,
        mode=job.mode,
        params=RenderParamsDTO(
            identity_weight=job.params.identity_weight,
            wavelet_high_pass=job.params.wavelet_high_pass,
            codeformer_fidelity=job.params.codeformer_fidelity,
            occlusion_masking=job.params.occlusion_masking,
            source_quadrant=job.params.source_quadrant,
        ),
        status=job.status,
        progress=job.progress,
        current_step=job.current_step,
        output_path=job.output_path,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.get("/stream/{job_id}")
async def stream_job_telemetry(job_id: str, request: Request):
    """Server-Sent Events endpoint for real-time progress and VRAM telemetry."""
    container = request.app.state.container
    return StreamingResponse(
        container.sse_manager.event_generator(job_id),
        media_type="text/event-stream",
    )
