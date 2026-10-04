"""In-memory fakes for adapters, so unit and contract tests never touch the network."""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from collections.abc import Sequence

from pmo_core.adapters import bm25
from pmo_core.models import Candidate, Chunk, IndexFilter, QueueMessage

FAKE_DIMENSIONS = 32


class FakeEmbeddings:
    """Deterministic hashed bag-of-words vectors (unit length)."""

    def __init__(self, dimensions: int = FAKE_DIMENSIONS) -> None:
        """Set the vector size."""
        self.dimensions = dimensions
        self.calls = 0

    def embed_query(self, text: str) -> list[float]:
        """Hash each token into a bucket, then normalize."""
        vector = [0.0] * self.dimensions
        for token in bm25.tokenize(text) or ["empty"]:
            bucket = int(hashlib.md5(token.encode()).hexdigest(), 16) % self.dimensions
            vector[bucket] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed each text."""
        self.calls += 1
        return [self.embed_query(text) for text in texts]


def _matches(chunk: Chunk, flt: IndexFilter) -> bool:
    """Same semantics as the Qdrant filter: any week or date; doc types required."""
    if flt.doc_types and chunk.doc_type not in flt.doc_types:
        return False
    if not (flt.weeks or flt.dates):
        return True
    return (chunk.week in flt.weeks) or (chunk.doc_date in flt.dates)


class FakeIndex:
    """Dictionary-backed `IndexBackend` with cosine dense search and BM25 keyword search."""

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
        """Cosine similarity over stored vectors."""
        scored = []
        for chunk_id, chunk in self.chunks.items():
            if _matches(chunk, flt):
                stored = self.vectors[chunk_id]
                dot = sum(a * b for a, b in zip(vector, stored, strict=True))
                norms = math.sqrt(sum(a * a for a in vector)) * math.sqrt(sum(b * b for b in stored)) or 1.0
                scored.append((dot / norms, chunk))
        scored.sort(key=lambda item: (-item[0], item[1].chunk_id))
        return [
            Candidate(chunk=chunk, dense_score=score, dense_rank=rank)
            for rank, (score, chunk) in enumerate(scored[:k], start=1)
        ]

    def keyword_search(self, query: str, k: int, flt: IndexFilter) -> list[Candidate]:
        """BM25 with IDF over the stored chunks (same encoder as Qdrant)."""
        query_terms = set(bm25.encode_query(query).indices)
        if not query_terms:
            return []
        doc_vectors = {cid: bm25.encode_document(chunk.text) for cid, chunk in self.chunks.items()}
        doc_freq: Counter[int] = Counter()
        for vector in doc_vectors.values():
            doc_freq.update(set(vector.indices))
        total = len(doc_vectors)
        scored = []
        for chunk_id, vector in doc_vectors.items():
            chunk = self.chunks[chunk_id]
            if not _matches(chunk, flt):
                continue
            weights = dict(zip(vector.indices, vector.values, strict=True))
            score = sum(
                weights[term] * math.log(1 + (total - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5))
                for term in query_terms
                if term in weights
            )
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda item: (-item[0], item[1].chunk_id))
        return [
            Candidate(chunk=chunk, keyword_score=score, keyword_rank=rank)
            for rank, (score, chunk) in enumerate(scored[:k], start=1)
        ]

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
