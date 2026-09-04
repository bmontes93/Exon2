"""Pydantic v2 schemas for System Status and Storage Path Configurations."""
from typing import Dict, Optional
from pydantic import BaseModel, Field


class DiskUsageDTO(BaseModel):
    """Storage capacity metrics."""
    total_gb: float
    used_gb: float
    free_gb: float


class VRAMUsageDTO(BaseModel):
    """GPU memory metrics."""
    total_mb: float
    allocated_mb: float
    reserved_mb: float
    free_mb: float


class SystemStatusResponse(BaseModel):
    """Overall system operational health and hardware state."""
    status: str
    vram: VRAMUsageDTO
    disk: DiskUsageDTO
    models_dir: str
    datasets_dir: str
    outputs_dir: str


class PathConfigUpdateRequest(BaseModel):
    """Request payload to update storage base directories dynamically."""
    models_dir: Optional[str] = Field(default=None, description="Path to AI models cache directory")
    datasets_dir: Optional[str] = Field(default=None, description="Path to datasets root directory")
    outputs_dir: Optional[str] = Field(default=None, description="Path to render outputs directory")
