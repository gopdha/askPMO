"""Worker loop: empty queue, normal handling, failures, poison messages."""

from __future__ import annotations

import pytest

from tests.fakes import FakeStorage
from worker.main import MAX_DEQUEUE, poll_once


class Recorder:
    """Collects handled and poisoned job IDs."""

    def __init__(self) -> None:
        """Start empty."""
        self.handled: list[str] = []
        self.poisoned: list[str] = []

    def handle(self, job_id: str) -> None:
        """Record a handled job."""
        self.handled.append(job_id)

    def poison(self, job_id: str) -> None:
        """Record a poisoned job."""
        self.poisoned.append(job_id)


def test_empty_queue_returns_false() -> None:
    """No message means nothing to do."""
    recorder = Recorder()
    assert poll_once(FakeStorage(), recorder.handle, recorder.poison) is False


def test_message_handled_then_deleted() -> None:
    """A normal message is handled and deleted."""
    storage, recorder = FakeStorage(), Recorder()
    storage.send("job-1")
    assert poll_once(storage, recorder.handle, recorder.poison) is True
    assert recorder.handled == ["job-1"]
    assert storage.deleted == ["1"]


def test_handler_failure_leaves_message() -> None:
    """If handling raises, the message is not deleted (it reappears after the visibility timeout)."""
    storage = FakeStorage()
    storage.send("job-1")

    def explode(job_id: str) -> None:
        """Simulated processing failure."""
        raise RuntimeError(job_id)

    with pytest.raises(RuntimeError):
        poll_once(storage, explode, Recorder().poison)
    assert storage.deleted == []


def test_poison_message_fails_job_and_is_deleted() -> None:
    """A message dequeued more than 3 times fails its job and is deleted, never handled."""
    storage, recorder = FakeStorage(), Recorder()
    storage.send("job-1", dequeue_count=MAX_DEQUEUE + 1)
    assert poll_once(storage, recorder.handle, recorder.poison) is True
    assert recorder.handled == []
    assert recorder.poisoned == ["job-1"]
    assert storage.deleted == ["1"]
