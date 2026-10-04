"""Worker loop: empty queue, poison messages."""

from __future__ import annotations

from tests.fakes import FakeStorage
from worker.main import MAX_DEQUEUE, poll_once


def test_empty_queue_returns_false() -> None:
    """No message means nothing to do."""
    assert poll_once(FakeStorage()) is False


def test_poison_message_deleted_without_handling() -> None:
    """A message dequeued more than 3 times is deleted, never handled."""
    storage = FakeStorage()
    storage.send("job-1", dequeue_count=MAX_DEQUEUE + 1)
    assert poll_once(storage) is True
    assert storage.deleted == ["1"]
