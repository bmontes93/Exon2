"""Server-Sent Events (SSE) Telemetry and Progress Streaming Manager."""
import asyncio
import json
from dataclasses import dataclass, asdict
from typing import Dict, Set, AsyncGenerator, Optional


@dataclass(frozen=True)
class TelemetryEvent:
    """Represents a real-time progress update event emitted by the synthesis engine."""
    step_name: str
    progress: float
    vram_allocated_mb: float = 0.0
    message: str = ""

    def to_sse_format(self) -> str:
        """Formats the payload according to the W3C Server-Sent Events specification."""
        payload = json.dumps(asdict(self))
        return f"data: {payload}\n\n"


class SSEManager:
    """
    Manages client subscriptions to per-job Server-Sent Events streams.
    Enables low-latency reactive telemetry to the frontend.
    """

    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, job_id: str) -> asyncio.Queue:
        """Subscribes a client connection to telemetry events for a specific job."""
        async with self._lock:
            if job_id not in self._subscribers:
                self._subscribers[job_id] = set()
            queue: asyncio.Queue = asyncio.Queue()
            self._subscribers[job_id].add(queue)
            return queue

    async def unsubscribe(self, job_id: str, queue: asyncio.Queue) -> None:
        """Removes a client connection queue upon disconnection."""
        async with self._lock:
            if job_id in self._subscribers and queue in self._subscribers[job_id]:
                self._subscribers[job_id].remove(queue)
                if not self._subscribers[job_id]:
                    del self._subscribers[job_id]

    async def publish(self, job_id: str, event: TelemetryEvent) -> None:
        """Broadcasts a telemetry event to all active subscribers for the job."""
        async with self._lock:
            queues = list(self._subscribers.get(job_id, []))

        for queue in queues:
            await queue.put(event)

    async def event_generator(self, job_id: str) -> AsyncGenerator[str, None]:
        """Async generator yielding formatted SSE text chunks for FastAPI StreamingResponse."""
        queue = await self.subscribe(job_id)
        try:
            while True:
                event = await queue.get()
                yield event.to_sse_format()
                if event.step_name in ["COMPLETED", "FAILED"]:
                    break
        finally:
            await self.unsubscribe(job_id, queue)
