"""Unit tests for the CUDA VRAM Sequential Orchestrator."""
import asyncio
import pytest
from unittest.mock import patch

from src.domain.exceptions import VRAMExceededException
from src.infrastructure.memory.vram_orchestrator import VRAMOrchestrator, VRAMStats


class TestVRAMOrchestrator:
    def test_default_initialization(self):
        orch = VRAMOrchestrator(max_vram_mb=8192, safe_threshold_mb=7168)
        assert orch.max_vram_mb == 8192
        assert orch.safe_threshold_mb == 7168
        assert orch.current_active_stage is None

    def test_get_memory_stats_fallback(self):
        orch = VRAMOrchestrator()
        stats = orch.get_vram_stats()
        assert isinstance(stats, VRAMStats)
        assert stats.total_mb >= 0
        assert stats.allocated_mb >= 0

    def test_acquire_and_release_slot(self):
        async def run_test():
            orch = VRAMOrchestrator(max_vram_mb=8192, safe_threshold_mb=7168)
            async with orch.acquire_slot("3D_DETECTION", estimated_mb=1200):
                assert orch.current_active_stage == "3D_DETECTION"
            # After exit, stage should be released
            assert orch.current_active_stage is None

        asyncio.run(run_test())

    def test_sequential_slot_concurrency_blocking(self):
        async def run_test():
            orch = VRAMOrchestrator()
            execution_order = []

            async def stage_one():
                async with orch.acquire_slot("STAGE_ONE", estimated_mb=2000):
                    execution_order.append("start_1")
                    await asyncio.sleep(0.05)
                    execution_order.append("end_1")

            async def stage_two():
                async with orch.acquire_slot("STAGE_TWO", estimated_mb=3000):
                    execution_order.append("start_2")
                    await asyncio.sleep(0.01)
                    execution_order.append("end_2")

            # Run both concurrently
            await asyncio.gather(stage_one(), stage_two())

            # Must execute strictly sequentially: 1 finishes before 2 starts
            assert execution_order == ["start_1", "end_1", "start_2", "end_2"]

        asyncio.run(run_test())

    def test_vram_exceeded_threshold_rejection(self):
        async def run_test():
            orch = VRAMOrchestrator(max_vram_mb=8192, safe_threshold_mb=7168)

            # Mock current memory usage as high (7000 MB)
            with patch.object(orch, "_get_allocated_cuda_mb", return_value=7000):
                with pytest.raises(VRAMExceededException) as exc_info:
                    async with orch.acquire_slot("HEAVY_DIFFUSION", estimated_mb=2500):
                        pass
                assert "VRAM allocation exceeded safety threshold" in str(exc_info.value)

        asyncio.run(run_test())
