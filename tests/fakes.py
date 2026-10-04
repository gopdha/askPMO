"""In-memory fakes for adapters, so unit and contract tests never touch the network."""

from __future__ import annotations

from collections.abc import Sequence

from pmo_core.models import Candidate, Chunk, IndexFilter, QueueMessage


class FakeIndex:
    """Dictionary-backed `IndexBackend` (search methods filled in with P1)."""

    def __init__(self, reachable: bool = True) -> None:
        """Start empty; `reachable=False` makes `ping` fail."""
        self.chunks: dict[str, Chunk] = {}
        self.vectors: dict[str, list[float]] = {}
        self.reachable = reachable
        self.schema_created = False

    def ping(self) -> None:
        """Fail when configured as unreachable."""
        if not self.reachable:
            raise ConnectionError("index down")

    def ensure_schema(self) -> None:
        """Record that the schema was created."""
        self.schema_created = True

    def upsert(self, chunks: Sequence[Chunk], dense: Sequence[list[float]]) -> None:
        """Store chunks by ID (idempotent)."""
        for chunk, vector in zip(chunks, dense, strict=True):
            self.chunks[chunk.chunk_id] = chunk
            self.vectors[chunk.chunk_id] = vector

    def delete_document(self, document_id: str) -> None:
        """Drop every chunk of one document."""
        for chunk_id in [cid for cid, chunk in self.chunks.items() if chunk.document_id == document_id]:
            del self.chunks[chunk_id]
            del self.vectors[chunk_id]

    def dense_search(self, vector: list[float], k: int, flt: IndexFilter) -> list[Candidate]:
        """Not needed before P1."""
        raise NotImplementedError

    def keyword_search(self, query: str, k: int, flt: IndexFilter) -> list[Candidate]:
        """Not needed before P1."""
        raise NotImplementedError

    def get_chunk(self, chunk_id: str) -> Chunk | None:
        """Look up a chunk."""
        return self.chunks.get(chunk_id)

    def count(self) -> int:
        """Number of stored chunks."""
        return len(self.chunks)


class FakeStorage:
    """In-memory `BlobStore` + `JobQueue`."""

    def __init__(self) -> None:
        """Start with no blobs and an empty queue."""
        self.blobs: dict[str, bytes] = {}
        self.messages: list[QueueMessage] = []
        self.deleted: list[str] = []
        self._next_id = 0

    def put(self, path: str, data: bytes, content_type: str) -> None:
        """Store bytes."""
        self.blobs[path] = data

    def get(self, path: str) -> bytes:
        """Read bytes."""
        return self.blobs[path]

    def send(self, job_id: str, dequeue_count: int = 1) -> None:
        """Enqueue a job ID."""
        self._next_id += 1
        self.messages.append(QueueMessage(str(self._next_id), "receipt", job_id, dequeue_count))

    def receive(self, visibility_timeout_s: int = 300) -> QueueMessage | None:
        """Pop the oldest message."""
        return self.messages.pop(0) if self.messages else None

    def delete(self, msg: QueueMessage) -> None:
        """Record the deletion."""
        self.deleted.append(msg.message_id)
