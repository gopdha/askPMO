"""Protocols that isolate everything that differs between local and Azure."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from pmo_core.models import Candidate, Chunk, IndexFilter, QueueMessage


class IndexBackend(Protocol):
    """Vector + keyword index (Qdrant locally, Azure AI Search on Azure)."""

    def ensure_schema(self) -> None:
        """Create the collection or index if missing."""
        ...

    def upsert(self, chunks: Sequence[Chunk], dense: Sequence[list[float]]) -> None:
        """Insert or replace chunks with their dense vectors."""
        ...

    def delete_document(self, document_id: str) -> None:
        """Remove every chunk of one document."""
        ...

    def dense_search(self, vector: list[float], k: int, flt: IndexFilter) -> list[Candidate]:
        """Return the top-k chunks by vector similarity."""
        ...

    def keyword_search(self, query: str, k: int, flt: IndexFilter) -> list[Candidate]:
        """Return the top-k chunks by keyword (BM25) score."""
        ...

    def get_chunk(self, chunk_id: str) -> Chunk | None:
        """Fetch one chunk by ID."""
        ...

    def count(self) -> int:
        """Return the number of indexed chunks."""
        ...

    def ping(self) -> None:
        """Raise if the backend is unreachable."""
        ...


class BlobStore(Protocol):
    """Raw document storage."""

    def put(self, path: str, data: bytes, content_type: str) -> None:
        """Store bytes at a path, overwriting."""
        ...

    def get(self, path: str) -> bytes:
        """Read bytes from a path."""
        ...


class JobQueue(Protocol):
    """Ingest job queue."""

    def send(self, job_id: str) -> None:
        """Enqueue a job ID."""
        ...

    def receive(self, visibility_timeout_s: int = 300) -> QueueMessage | None:
        """Receive one message, hiding it for the visibility timeout."""
        ...

    def delete(self, msg: QueueMessage) -> None:
        """Delete a processed message."""
        ...


class Embedder(Protocol):
    """Embedding model (LangChain `Embeddings`-compatible)."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed many texts."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Embed one query."""
        ...
