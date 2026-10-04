"""Qdrant implementation of `IndexBackend` (named dense vector + sparse BM25 vector)."""

from __future__ import annotations

from collections.abc import Sequence

from qdrant_client import QdrantClient, models

from pmo_core.models import Candidate, Chunk, IndexFilter

DENSE_VECTOR = "dense"
SPARSE_VECTOR = "bm25"

PAYLOAD_INDEXES: dict[str, models.PayloadSchemaType] = {
    "document_id": models.PayloadSchemaType.KEYWORD,
    "doc_type": models.PayloadSchemaType.KEYWORD,
    "week": models.PayloadSchemaType.INTEGER,
    "doc_date": models.PayloadSchemaType.DATETIME,
    "ids": models.PayloadSchemaType.KEYWORD,
}


class QdrantIndex:
    """Chunk index backed by a Qdrant collection."""

    def __init__(self, url: str, collection: str, dimensions: int, timeout_s: int = 10) -> None:
        """Create a client; no network calls happen until a method is used."""
        self.client = QdrantClient(url=url, timeout=timeout_s)
        self.collection = collection
        self.dimensions = dimensions

    def ping(self) -> None:
        """Raise if Qdrant is unreachable."""
        self.client.get_collections()

    def ensure_schema(self) -> None:
        """Create the collection and payload indexes if they do not exist."""
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config={
                    DENSE_VECTOR: models.VectorParams(size=self.dimensions, distance=models.Distance.COSINE)
                },
                sparse_vectors_config={
                    SPARSE_VECTOR: models.SparseVectorParams(modifier=models.Modifier.IDF)
                },
            )
        for field_name, schema in PAYLOAD_INDEXES.items():
            self.client.create_payload_index(self.collection, field_name=field_name, field_schema=schema)

    def count(self) -> int:
        """Return the number of points in the collection."""
        return self.client.count(self.collection, exact=True).count

    def upsert(self, chunks: Sequence[Chunk], dense: Sequence[list[float]]) -> None:
        """Insert or replace chunks (implemented in P1)."""
        raise NotImplementedError("P1")

    def delete_document(self, document_id: str) -> None:
        """Remove every chunk of one document (implemented in P1)."""
        raise NotImplementedError("P1")

    def dense_search(self, vector: list[float], k: int, flt: IndexFilter) -> list[Candidate]:
        """Vector search (implemented in P1)."""
        raise NotImplementedError("P1")

    def keyword_search(self, query: str, k: int, flt: IndexFilter) -> list[Candidate]:
        """BM25 search (implemented in P1/P4)."""
        raise NotImplementedError("P1")

    def get_chunk(self, chunk_id: str) -> Chunk | None:
        """Fetch one chunk by ID (implemented in P1)."""
        raise NotImplementedError("P1")
