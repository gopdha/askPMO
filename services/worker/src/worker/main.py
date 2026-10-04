"""Queue loop: receives ingest job IDs and processes them."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable

import structlog

from pmo_core import telemetry
from pmo_core.adapters.base import JobQueue
from pmo_core.container import Container, build_container, require_embedder, require_engine
from pmo_core.ingest.jobs import mark_job_failed, process_job
from pmo_core.settings import get_settings

_logger = structlog.get_logger(__name__)
POLL_INTERVAL_S = 2.0
VISIBILITY_TIMEOUT_S = 300
MAX_DEQUEUE = 3


def poll_once(queue: JobQueue, handle: Callable[[str], None], on_poison: Callable[[str], None]) -> bool:
    """Receive and handle at most one message; return True when one was received.

    A message dequeued more than `MAX_DEQUEUE` times marks its job failed and is deleted.
    If `handle` raises, the message is left on the queue and reappears after the visibility timeout.
    """
    message = queue.receive(VISIBILITY_TIMEOUT_S)
    if message is None:
        return False
    if message.dequeue_count > MAX_DEQUEUE:
        _logger.error("poison_message", job_id=message.job_id, dequeue_count=message.dequeue_count)
        on_poison(message.job_id)
        queue.delete(message)
        return True
    handle(message.job_id)
    queue.delete(message)
    return True


def job_handlers(container: Container) -> tuple[Callable[[str], None], Callable[[str], None]]:
    """Bind the job processor and the poison handler to the container's adapters."""
    engine = require_engine(container)
    embedder = require_embedder(container)

    def handle(job_id: str) -> None:
        """Process one ingest job."""
        process_job(engine, container.blobs, container.index, embedder, uuid.UUID(job_id))

    def on_poison(job_id: str) -> None:
        """Fail the job of a message that keeps coming back."""
        mark_job_failed(engine, uuid.UUID(job_id), f"message dequeued more than {MAX_DEQUEUE} times")

    return handle, on_poison


def main() -> None:
    """Run the worker loop forever."""
    settings = get_settings()
    telemetry.setup("worker", settings)
    container = build_container(settings)
    handle, on_poison = job_handlers(container)
    _logger.info("worker_started", queue=settings.ingest_queue)
    while True:
        try:
            if not poll_once(container.queue, handle, on_poison):
                time.sleep(POLL_INTERVAL_S)
        except Exception as exc:
            _logger.error("worker_error", error_type=type(exc).__name__, error=str(exc)[:200])
            time.sleep(POLL_INTERVAL_S)
