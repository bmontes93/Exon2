"""Pydantic v2 schemas for Render Execution and Job Status."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from src.domain.enums import AngleQuadrant, RenderMode, JobStatus


class RenderParamsDTO(BaseModel):
    """Parameters for fine-tuning the synthesis pipeline."""
    identity_weight: float = Field(default=1.0, ge=0.0, le=2.0, description="Identity injection strength")
    wavelet_high_pass: float = Field(default=1.0, ge=0.0, le=3.0, description="High-pass texture retention gain")
    codeformer_fidelity: float = Field(default=0.75, ge=0.0, le=1.0, description="Restoration fidelity ratio")
    occlusion_masking: bool = Field(default=True, description="Enable BiSeNet occlusion segmentation")
    source_quadrant: Optional[AngleQuadrant] = Field(default=None, description="Force a specific angle quadrant")


class RenderExecuteRequest(BaseModel):
    """Request payload to initiate a face swap render."""
    subject_id: str = Field(..., min_length=1, description="Subject ID from catalog")
    mode: RenderMode = Field(default=RenderMode.EXPRESS, description="Synthesis execution mode")
    params: RenderParamsDTO = Field(default_factory=RenderParamsDTO, description="Studio parameter weights")


class RenderJobResponse(BaseModel):
    """Status and result details for a render job."""
    job_id: str
    subject_id: str
    target_image_path: str
    mode: RenderMode
    params: RenderParamsDTO
    status: JobStatus
    progress: float
    current_step: str
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
