"""One contract suite for every `IndexBackend`: the in-memory fake and Qdrant (AI Search joins in P7)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import date

import pytest

from pmo_core.adapters.base import IndexBackend
from pmo_core.adapters.index_qdrant import QdrantIndex
from pmo_core.models import Chunk, IndexFilter
from tests.fakes import FAKE_DIMENSIONS, FakeEmbeddings, FakeIndex

EMBEDDINGS = FakeEmbeddings(FAKE_DIMENSIONS)


def _chunk(
    document_id: str, number: int, text: str, week: int | None = None, day: date | None = None
) -> Chunk:
    """Build a chunk with IDs parsed from its text."""
    from pmo_core.ingest.metadata import item_ids

    return Chunk(
        chunk_id=f"{document_id}:{number}",
        document_id=document_id,
        text=text,
        source=f"{document_id}.md",
        section=f"section {number}",
        doc_type="status_report" if week else "raid_log",
        doc_date=day,
        week=week,
        ids=item_ids(text),
    )


CHUNKS = [
    _chunk("wk05", 0, "[Status – Week 5 — Summary] Data migration is amber.", 5, date(2026, 2, 13)),
    _chunk(
        "wk06",
        0,
        "[Status – Week 6 — Summary] Data migration is red; ISS-009 throughput.",
        6,
        date(2026, 2, 20),
    ),
    _chunk("wk06", 1, "[Status – Week 6 — Risks] Connector delivery slipping.", 6, date(2026, 2, 20)),
    _chunk("raid", 0, "RAID item RSK-014 (Risk) | Mitigation: weekly executive call with DataBridge."),
    _chunk("raid", 1, "RAID item RSK-015 (Risk) | Mitigation: backfill lead data architect."),
]


@pytest.fixture(params=["fake", "qdrant"])
def index(request: pytest.FixtureRequest) -> Iterator[IndexBackend]:
    """A fresh, empty index of each backend."""
    if request.param == "fake":
        yield FakeIndex()
        return
    qdrant_url: str = request.getfixturevalue("qdrant_url")
    backend = QdrantIndex(qdrant_url, f"contract_{uuid.uuid4().hex[:8]}", FAKE_DIMENSIONS)
    backend.ensure_schema()
    yield backend
    backend.client.delete_collection(backend.collection)


def _load(index: IndexBackend, chunks: list[Chunk] = CHUNKS) -> None:
    """Upsert chunks with fake embeddings."""
    index.upsert(chunks, EMBEDDINGS.embed_documents([chunk.text for chunk in chunks]))


def test_ensure_schema_is_idempotent(index: IndexBackend) -> None:
    """Calling ensure_schema twice is safe."""
    index.ensure_schema()
    assert index.count() == 0


def test_upsert_is_idempotent(index: IndexBackend) -> None:
    """Upserting the same chunks twice does not duplicate them."""
    _load(index)
    _load(index)
    assert index.count() == len(CHUNKS)


def test_get_chunk_round_trip(index: IndexBackend) -> None:
    """Chunks come back with all fields intact."""
    _load(index)
    assert index.get_chunk("wk06:0") == CHUNKS[1]
    assert index.get_chunk("missing:0") is None


def test_keyword_match_on_item_id(index: IndexBackend) -> None:
    """A keyword search for RSK-014 ranks that RAID row first."""
    _load(index)
    results = index.keyword_search("What is the mitigation for RSK-014?", 5, IndexFilter())
    assert results[0].chunk.chunk_id == "raid:0"
    assert results[0].keyword_rank == 1
    assert results[0].keyword_score is not None and results[0].keyword_score > 0


def test_dense_search_ranks_and_scores(index: IndexBackend) -> None:
    """Dense search returns ranked candidates with scores, best first."""
    _load(index)
    results = index.dense_search(EMBEDDINGS.embed_query(CHUNKS[3].text), 3, IndexFilter())
    assert results[0].chunk.chunk_id == "raid:0"
    assert [candidate.dense_rank for candidate in results] == [1, 2, 3]
    scores = [candidate.dense_score or 0.0 for candidate in results]
    assert scores == sorted(scores, reverse=True)


def test_week_filter(index: IndexBackend) -> None:
    """A week filter restricts both legs to that week's chunks."""
    _load(index)
    flt = IndexFilter(weeks=(6,))
    dense = index.dense_search(EMBEDDINGS.embed_query("data migration"), 10, flt)
    keyword = index.keyword_search("data migration", 10, flt)
    assert {candidate.chunk.document_id for candidate in dense} == {"wk06"}
    assert {candidate.chunk.document_id for candidate in keyword} == {"wk06"}


def test_date_or_week_filter(index: IndexBackend) -> None:
    """Weeks and dates combine with OR."""
    _load(index)
    flt = IndexFilter(weeks=(6,), dates=(date(2026, 2, 13),))
    dense = index.dense_search(EMBEDDINGS.embed_query("data migration"), 10, flt)
    assert {candidate.chunk.document_id for candidate in dense} == {"wk05", "wk06"}


def test_doc_type_filter(index: IndexBackend) -> None:
    """Doc types are a hard constraint."""
    _load(index)
    dense = index.dense_search(EMBEDDINGS.embed_query("mitigation"), 10, IndexFilter(doc_types=("raid_log",)))
    assert {candidate.chunk.doc_type for candidate in dense} == {"raid_log"}


def test_delete_document(index: IndexBackend) -> None:
    """Deleting a document removes all and only its chunks."""
    _load(index)
    index.delete_document("wk06")
    assert index.count() == len(CHUNKS) - 2
    assert index.get_chunk("wk06:0") is None
    assert index.get_chunk("wk05:0") is not None
