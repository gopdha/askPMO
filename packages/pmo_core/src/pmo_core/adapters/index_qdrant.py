"""Qdrant implementation of `IndexBackend` (named dense vector + sparse BM25 vector)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, date, datetime, time
from typing import Any

from qdrant_client import QdrantClient, models

from pmo_core.adapters import bm25
from pmo_core.models import Candidate, Chunk, IndexFilter

DENSE_VECTOR = "dense"
SPARSE_VECTOR = "bm25"
POINT_NAMESPACE = uuid.UUID("6f1c3c1e-6d8a-4b8e-9a0e-5b7f6a2d4c11")

PAYLOAD_INDEXES: dict[str, models.PayloadSchemaType] = {
    "document_id": models.PayloadSchemaType.KEYWORD,
    "doc_type": models.PayloadSchemaType.KEYWORD,
    "week": models.PayloadSchemaType.INTEGER,
    "doc_date": models.PayloadSchemaType.DATETIME,
    "ids": models.PayloadSchemaType.KEYWORD,
}


def point_id(chunk_id: str) -> str:
    """UUIDv5 from the chunk ID, so upserts are idempotent."""
    return str(uuid.uuid5(POINT_NAMESPACE, chunk_id))


def chunk_to_payload(chunk: Chunk) -> dict[str, Any]:
    """Serialize a chunk to the Qdrant payload."""
    return {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "text": chunk.text,
        "source": chunk.source,
        "section": chunk.section,
        "doc_type": chunk.doc_type,
        "doc_date": chunk.doc_date.isoformat() if chunk.doc_date else None,
        "week": chunk.week,
        "ids": list(chunk.ids),
    }


def payload_to_chunk(payload: dict[str, Any]) -> Chunk:
    """Rebuild a chunk from its payload."""
    raw_date = payload.get("doc_date")
    return Chunk(
        chunk_id=payload["chunk_id"],
        document_id=payload["document_id"],
        text=payload["text"],
        source=payload["source"],
        section=payload["section"],
        doc_type=payload["doc_type"],
        doc_date=date.fromisoformat(raw_date[:10]) if raw_date else None,
        week=payload.get("week"),
        ids=tuple(payload.get("ids") or ()),
    )


def build_filter(flt: IndexFilter) -> models.Filter | None:
    """Match any requested week or date; doc types are a hard constraint."""
    if flt.is_empty():
        return None
    should: list[models.Condition] = []
    if flt.weeks:
        should.append(models.FieldCondition(key="week", match=models.MatchAny(any=list(flt.weeks))))
    for day in flt.dates:
        start = datetime.combine(day, time.min, tzinfo=UTC)
        end = datetime.combine(day, time.max, tzinfo=UTC)
        should.append(models.FieldCondition(key="doc_date", range=models.DatetimeRange(gte=start, lte=end)))
    must: list[models.Condition] = []
    if flt.doc_types:
        must.append(models.FieldCondition(key="doc_type", match=models.MatchAny(any=list(flt.doc_types))))
    return models.Filter(should=should or None, must=must or None)


class QdrantIndex:
    """Chunk index backed by a Qdrant collection."""

    def __init__(self, url: str, collection: str, dimensions: int, timeout_s: int = 30) -> None:
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
        """Insert or replace chunks with dense and BM25 vectors."""
        points = []
        for chunk, vector in zip(chunks, dense, strict=True):
            sparse = bm25.encode_document(chunk.text)
            points.append(
                models.PointStruct(
                    id=point_id(chunk.chunk_id),
                    vector={
                        DENSE_VECTOR: vector,
                        SPARSE_VECTOR: models.SparseVector(indices=sparse.indices, values=sparse.values),
                    },
                    payload=chunk_to_payload(chunk),
                )
            )
        self.client.upsert(self.collection, points=points, wait=True)

    def delete_document(self, document_id: str) -> None:
        """Remove every chunk of one document."""
        selector = models.FilterSelector(
            filter=models.Filter(
                must=[models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id))]
            )
        )
        self.client.delete(self.collection, points_selector=selector, wait=True)

    def _query(self, query: Any, using: str, k: int, flt: IndexFilter) -> list[models.ScoredPoint]:
        """Run one Query API request against a named vector."""
        response = self.client.query_points(
            self.collection,
            query=query,
            using=using,
            limit=k,
            query_filter=build_filter(flt),
            with_payload=True,
        )
        return response.points

    def dense_search(self, vector: list[float], k: int, flt: IndexFilter) -> list[Candidate]:
        """Top-k chunks by cosine similarity."""
        points = self._query(vector, DENSE_VECTOR, k, flt)
        return [
            Candidate(chunk=payload_to_chunk(point.payload or {}), dense_score=point.score, dense_rank=rank)
            for rank, point in enumerate(points, start=1)
        ]

    def keyword_search(self, query: str, k: int, flt: IndexFilter) -> list[Candidate]:
        """Top-k chunks by BM25 (IDF applied by Qdrant)."""
        sparse = bm25.encode_query(query)
        if not sparse.indices:
            return []
        points = self._query(
            models.SparseVector(indices=sparse.indices, values=sparse.values), SPARSE_VECTOR, k, flt
        )
        return [
            Candidate(
                chunk=payload_to_chunk(point.payload or {}), keyword_score=point.score, keyword_rank=rank
            )
            for rank, point in enumerate(points, start=1)
        ]

    def get_chunk(self, chunk_id: str) -> Chunk | None:
        """Fetch one chunk by ID."""
        records = self.client.retrieve(self.collection, ids=[point_id(chunk_id)], with_payload=True)
        return payload_to_chunk(records[0].payload or {}) if records else None
