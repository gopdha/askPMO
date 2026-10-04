"""Domain types shared by ingestion, the query pipeline and evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class Chunk:
    """One indexed piece of a document."""

    chunk_id: str  # "{document_id}:{chunk_no}"
    document_id: str
    text: str  # includes the contextual header line
    source: str  # original filename
    section: str  # header path, "page 3", or RAID row ID
    doc_type: str
    doc_date: date | None
    week: int | None
    ids: tuple[str, ...]  # item IDs found in the text


@dataclass
class Candidate:
    """A chunk with the scores it collected on its way through the pipeline."""

    chunk: Chunk
    dense_score: float | None = None
    keyword_score: float | None = None
    dense_rank: int | None = None
    keyword_rank: int | None = None
    fused_score: float | None = None
    rerank_score: float | None = None  # sigmoid-normalized, 0..1
    final_score: float | None = None  # rerank + recency boost


@dataclass
class StageTrace:
    """What one pipeline stage did and how long it took."""

    stage: str  # rewrite | filter | retrieve | rerank | guardrail | generate
    ms: int
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IndexFilter:
    """Metadata filter applied to both retrieval legs (match on any week or any date)."""

    weeks: tuple[int, ...] = ()
    dates: tuple[date, ...] = ()
    doc_types: tuple[str, ...] = ()

    def is_empty(self) -> bool:
        """Return True when the filter restricts nothing."""
        return not (self.weeks or self.dates or self.doc_types)


@dataclass(frozen=True)
class QueueMessage:
    """A message received from the ingest queue."""

    message_id: str
    pop_receipt: str
    job_id: str
    dequeue_count: int
