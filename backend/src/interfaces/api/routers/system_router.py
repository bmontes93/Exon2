"""System status and storage paths configuration router."""
from fastapi import APIRouter, Depends, Request
from src.interfaces.schemas.system_schemas import (
    SystemStatusResponse,
    PathConfigUpdateRequest,
    DiskUsageDTO,
    VRAMUsageDTO,
)

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(request: Request):
    """Retrieves hardware and storage diagnostics."""
    container = request.app.state.container
    storage = container.storage_adapter
    vram = container.vram_orchestrator

    disk_info = storage.get_disk_metrics()
    vram_stats = vram.get_vram_stats()

    return SystemStatusResponse(
        status="ONLINE",
        vram=VRAMUsageDTO(
            total_mb=vram_stats.total_mb,
            allocated_mb=vram_stats.allocated_mb,
            reserved_mb=vram_stats.reserved_mb,
            free_mb=vram_stats.free_mb,
        ),
        disk=DiskUsageDTO(
            total_gb=disk_info["total_gb"],
            used_gb=disk_info["used_gb"],
            free_gb=disk_info["free_gb"],
        ),
        models_dir=str(storage.models_dir),
        datasets_dir=str(storage.datasets_dir),
        outputs_dir=str(storage.outputs_dir),
    )


@router.post("/config/paths", response_model=SystemStatusResponse)
async def update_system_paths(payload: PathConfigUpdateRequest, request: Request):
    """Dynamically updates storage root directories."""
    container = request.app.state.container
    storage = container.storage_adapter

    storage.update_paths(
        models_dir=payload.models_dir,
        datasets_dir=payload.datasets_dir,
        outputs_dir=payload.outputs_dir,
    )
    return await get_system_status(request)
