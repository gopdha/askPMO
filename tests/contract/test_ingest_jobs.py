"""Upload registration and job processing against a real Postgres (fake index, blobs and embeddings)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, delete, select

from pmo_core.db import make_engine
from pmo_core.db.tables import documents, ingest_jobs
from pmo_core.ingest.jobs import (
    UploadedFile,
    mark_job_failed,
    normalize_rel_path,
    process_job,
    register_upload,
)
from tests.conftest import REPO_ROOT
from tests.fakes import FakeEmbeddings, FakeIndex, FakeStorage

CORPUS = REPO_ROOT / "corpus"
REPORT = "02_status_reports/status_report_wk06_2026-02-20.md"
RAID = "03_raid/raid_log_2026-04-03.csv"


@pytest.fixture
def engine(database_url: str) -> Iterator[Engine]:
    """An engine on a clean database."""
    engine = make_engine(database_url)
    with engine.begin() as connection:
        connection.execute(delete(ingest_jobs))
        connection.execute(delete(documents))
    yield engine
    engine.dispose()


def _file(rel_path: str, data: bytes | None = None) -> UploadedFile:
    """An upload of a corpus file (or custom bytes)."""
    return UploadedFile(rel_path, data if data is not None else (CORPUS / rel_path).read_bytes())


def _job(engine: Engine, job_id: uuid.UUID) -> object:
    """Fetch a job row."""
    with engine.connect() as connection:
        return connection.execute(select(ingest_jobs).where(ingest_jobs.c.id == job_id)).one()


def test_upload_then_process(engine: Engine) -> None:
    """Upload stores blobs and rows; processing indexes chunks and fills metadata and counters."""
    blobs, index, embedder = FakeStorage(), FakeIndex(), FakeEmbeddings()
    result = register_upload(engine, blobs, [_file(REPORT), _file(RAID)])
    assert len(result.document_ids) == 2
    assert len(blobs.blobs) == 2
    assert process_job(engine, blobs, index, embedder, result.job_id) == "succeeded"
    job = _job(engine, result.job_id)
    assert job.documents_done == 2  # type: ignore[attr-defined]
    assert job.chunks_written == index.count() > 18  # type: ignore[attr-defined]
    with engine.connect() as connection:
        rows = {row.rel_path: row for row in connection.execute(select(documents))}
    assert rows[REPORT].status == "indexed"
    assert rows[REPORT].week == 6
    assert rows[RAID].doc_type == "raid_log"
    assert rows[RAID].chunk_count == 18


def test_unchanged_reupload_skipped_and_changed_replaced(engine: Engine) -> None:
    """Same hash is skipped; a different hash keeps the document ID and replaces its chunks."""
    blobs, index, embedder = FakeStorage(), FakeIndex(), FakeEmbeddings()
    first = register_upload(engine, blobs, [_file(REPORT)])
    process_job(engine, blobs, index, embedder, first.job_id)
    again = register_upload(engine, blobs, [_file(REPORT)])
    assert again.document_ids == [] and again.skipped == [REPORT]
    assert _job(engine, again.job_id).status == "succeeded"  # type: ignore[attr-defined]
    changed = register_upload(engine, blobs, [_file(REPORT, b"# Status\n\n## Summary\n\nAll green now.")])
    assert changed.document_ids == first.document_ids
    process_job(engine, blobs, index, embedder, changed.job_id)
    assert index.count() == 1
    assert "All green now." in next(iter(index.chunks.values())).text


def test_bad_document_fails_job_but_others_index(engine: Engine) -> None:
    """A document that cannot be parsed marks the job failed; other documents still index."""
    blobs, index, embedder = FakeStorage(), FakeIndex(), FakeEmbeddings()
    result = register_upload(
        engine, blobs, [_file("06_finance_resourcing/broken.pdf", b"not a pdf"), _file(RAID)]
    )
    assert process_job(engine, blobs, index, embedder, result.job_id) == "failed"
    job = _job(engine, result.job_id)
    assert "broken.pdf" in (job.error or "")  # type: ignore[attr-defined]
    assert index.count() == 18


def test_mark_job_failed(engine: Engine) -> None:
    """Poison handling marks the job failed with a reason."""
    result = register_upload(engine, FakeStorage(), [_file(RAID)])
    mark_job_failed(engine, result.job_id, "dequeued too often")
    job = _job(engine, result.job_id)
    assert job.status == "failed" and job.error == "dequeued too often"  # type: ignore[attr-defined]


def test_normalize_rel_path() -> None:
    """Paths are normalized and traversal is rejected."""
    assert normalize_rel_path("corpus\\03_raid\\raid.csv") == "03_raid/raid.csv"
    with pytest.raises(ValueError):
        normalize_rel_path("../etc/passwd")
