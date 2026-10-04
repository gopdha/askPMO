"""Queue loop: receives ingest job IDs and processes them (processing arrives in P1)."""

from __future__ import annotations

import time

import structlog

from pmo_core import telemetry
from pmo_core.adapters.base import JobQueue
from pmo_core.container import build_container
from pmo_core.models import QueueMessage
from pmo_core.settings import get_settings

_logger = structlog.get_logger(__name__)
POLL_INTERVAL_S = 2.0
VISIBILITY_TIMEOUT_S = 300
MAX_DEQUEUE = 3


def handle(message: QueueMessage) -> None:
    """Process one ingest job (implemented in P1)."""
    raise NotImplementedError("Ingestion arrives in P1")


def poll_once(queue: JobQueue) -> bool:
    """Receive and handle at most one message; return True when one was received."""
    message = queue.receive(VISIBILITY_TIMEOUT_S)
    if message is None:
        return False
    if message.dequeue_count > MAX_DEQUEUE:
        _logger.error("poison_message", job_id=message.job_id, dequeue_count=message.dequeue_count)
        queue.delete(message)
        return True
    handle(message)
    queue.delete(message)
    return True


def main() -> None:
    """Run the worker loop forever."""
    settings = get_settings()
    telemetry.setup("worker", settings)
    container = build_container(settings)
    _logger.info("worker_started", queue=settings.ingest_queue)
    while True:
        try:
            if not poll_once(container.queue):
                time.sleep(POLL_INTERVAL_S)
        except Exception as exc:
            _logger.error("worker_error", error_type=type(exc).__name__)
            time.sleep(POLL_INTERVAL_S)
