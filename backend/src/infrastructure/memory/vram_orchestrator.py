"""CUDA VRAM Sequential Orchestrator and Memory Guard."""
import asyncio
import gc
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

from src.domain.exceptions import VRAMExceededException

logger = logging.getLogger("exon.memory")


@dataclass(frozen=True)
class VRAMStats:
    """Current snapshot of GPU VRAM metrics."""
    total_mb: float
    allocated_mb: float
    reserved_mb: float
    free_mb: float


class VRAMOrchestrator:
    """
    Ensures sequential access to GPU VRAM and enforces memory limits.
    Guarantees cleanup and garbage collection upon stage exit.
    """

    def __init__(self, max_vram_mb: int = 8192, safe_threshold_mb: int = 7168):
        self.max_vram_mb = max_vram_mb
        self.safe_threshold_mb = safe_threshold_mb
        self._lock = asyncio.Lock()
        self.current_active_stage: Optional[str] = None

    def _get_allocated_cuda_mb(self) -> float:
        """Retrieves currently allocated CUDA memory in megabytes."""
        try:
            import torch
            if torch.cuda.is_available():
                return torch.cuda.memory_allocated() / (1024 * 1024)
        except ImportError:
            pass
        return 0.0

    def _get_total_cuda_mb(self) -> float:
        """Retrieves total CUDA memory in megabytes."""
        try:
            import torch
            if torch.cuda.is_available():
                return torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
        except ImportError:
            pass
        return float(self.max_vram_mb)

    def get_vram_stats(self) -> VRAMStats:
        """Returns the current VRAM statistics snapshot."""
        total = self._get_total_cuda_mb()
        allocated = self._get_allocated_cuda_mb()
        reserved = allocated
        try:
            import torch
            if torch.cuda.is_available():
                reserved = torch.cuda.memory_reserved() / (1024 * 1024)
        except ImportError:
            pass
        free = max(0.0, total - allocated)
        return VRAMStats(
            total_mb=total,
            allocated_mb=allocated,
            reserved_mb=reserved,
            free_mb=free,
        )

    def clean_cache(self) -> None:
        """Forces Python GC and CUDA cache emptying."""
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
        except ImportError:
            pass

    @asynccontextmanager
    async def acquire_slot(
        self, stage_name: str, estimated_mb: int = 1000
    ) -> AsyncGenerator[None, None]:
        """
        Asynchronously acquires the exclusive execution slot for a pipeline stage.
        Verifies that estimated memory will not exceed the safe threshold.
        """
        async with self._lock:
            # Check current VRAM baseline
            current_allocated = self._get_allocated_cuda_mb()
            if current_allocated + estimated_mb > self.safe_threshold_mb:
                raise VRAMExceededException(
                    f"VRAM allocation exceeded safety threshold: current {current_allocated:.1f} MB + "
                    f"estimated {estimated_mb} MB > limit {self.safe_threshold_mb} MB"
                )

            self.current_active_stage = stage_name
            logger.info(
                f"[VRAMOrchestrator] Acquired slot for stage '{stage_name}' (Est: {estimated_mb}MB)"
            )
            try:
                yield
            finally:
                logger.info(f"[VRAMOrchestrator] Releasing stage '{stage_name}' and clearing cache")
                self.clean_cache()
                self.current_active_stage = None
