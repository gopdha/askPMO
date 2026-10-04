"""Upload registration (api side) and ingest job processing (worker side)."""

from __future__ import annotations

import mimetypes
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any

import structlog
from sqlalchemy import Engine, select, update
from sqlalchemy.dialects.postgresql import insert

from pmo_core.adapters.base import BlobStore, Embedder, IndexBackend
from pmo_core.db.tables import documents, ingest_jobs
from pmo_core.ingest.pipeline import chunk_document, content_hash, index_document

_logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class UploadedFile:
    """One file from a multipart upload."""

    rel_path: str
    data: bytes


@dataclass(frozen=True)
class UploadResult:
    """The job created for an upload and the documents it will (re)index."""

    job_id: uuid.UUID
    document_ids: list[uuid.UUID]
    skipped: list[str]


def normalize_rel_path(rel_path: str) -> str:
    """Forward slashes, no leading slash or `corpus/` prefix, no parent references."""
    path = rel_path.replace("\\", "/").lstrip("/")
    if path.startswith("corpus/"):
        path = path[len("corpus/") :]
    if not path or ".." in PurePosixPath(path).parts:
        raise ValueError(f"Invalid relative path: {rel_path!r}")
    return path


def _now() -> datetime:
    """Current UTC time."""
    return datetime.now(UTC)


def register_upload(engine: Engine, blobs: BlobStore, files: Sequence[UploadedFile]) -> UploadResult:
    """Store new or changed files, upsert their document rows and create one ingest job.

    A file whose `rel_path` already exists with the same content hash (and is indexed) is skipped.
    """
    document_ids: list[uuid.UUID] = []
    skipped: list[str] = []
    with engine.begin() as connection:
        for upload in files:
            rel_path = normalize_rel_path(upload.rel_path)
            digest = content_hash(upload.data)
            existing = connection.execute(
                select(documents.c.id, documents.c.content_hash, documents.c.status).where(
                    documents.c.rel_path == rel_path
                )
            ).first()
            if existing is not None and existing.content_hash == digest and existing.status == "indexed":
                skipped.append(rel_path)
                continue
            document_id = existing.id if existing is not None else uuid.uuid4()
            filename = PurePosixPath(rel_path).name
            blob_path = f"raw/{document_id}/{filename}"
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            blobs.put(blob_path, upload.data, content_type)
            values: dict[str, Any] = {
                "id": document_id,
                "filename": filename,
                "rel_path": rel_path,
                "blob_path": blob_path,
                "content_hash": digest,
                "status": "uploaded",
            }
            statement = insert(documents).values(**values)
            connection.execute(
                statement.on_conflict_do_update(
                    index_elements=[documents.c.rel_path],
                    set_={key: statement.excluded[key] for key in values if key not in {"id", "rel_path"}},
                )
            )
            document_ids.append(document_id)
        job_id = uuid.uuid4()
        connection.execute(
            ingest_jobs.insert().values(
                id=job_id,
                status="queued" if document_ids else "succeeded",
                document_ids=document_ids,
                finished_at=None if document_ids else _now(),
            )
        )
    return UploadResult(job_id, document_ids, skipped)


def mark_job_failed(engine: Engine, job_id: uuid.UUID, error: str) -> None:
    """Mark a job failed (used for poison messages)."""
    with engine.begin() as connection:
        connection.execute(
            update(ingest_jobs)
            .where(ingest_jobs.c.id == job_id)
            .values(status="failed", error=error[:1000], finished_at=_now())
        )


def process_job(
    engine: Engine, blobs: BlobStore, index: IndexBackend, embedder: Embedder, job_id: uuid.UUID
) -> str:
    """Ingest every document of a job; returns the final job status."""
    with engine.begin() as connection:
        job = connection.execute(select(ingest_jobs).where(ingest_jobs.c.id == job_id)).first()
        if job is None:
            _logger.warning("job_not_found", job_id=str(job_id))
            return "missing"
        if job.status in {"succeeded", "failed"}:
            return str(job.status)
        connection.execute(
            update(ingest_jobs)
            .where(ingest_jobs.c.id == job_id)
            .values(status="running", started_at=_now(), documents_done=0, chunks_written=0, error=None)
        )
    errors: list[str] = []
    for document_id in job.document_ids:
        with engine.connect() as connection:
            document = connection.execute(select(documents).where(documents.c.id == document_id)).first()
        if document is None:
            errors.append(f"{document_id}: document row missing")
            continue
        try:
            processed = chunk_document(str(document_id), document.rel_path, blobs.get(document.blob_path))
            written = index_document(index, embedder, processed, str(document_id))
            document_values: dict[str, Any] = {
                "status": "indexed",
                "chunk_count": written,
                "doc_type": processed.metadata.doc_type,
                "doc_date": processed.metadata.doc_date,
                "week": processed.metadata.week,
            }
        except Exception as exc:
            _logger.error("document_failed", document_id=str(document_id), error_type=type(exc).__name__)
            errors.append(f"{document.rel_path}: {type(exc).__name__}: {str(exc)[:200]}")
            written = 0
            document_values = {"status": "failed", "chunk_count": 0}
        with engine.begin() as connection:
            connection.execute(
                update(documents).where(documents.c.id == document_id).values(**document_values)
            )
            connection.execute(
                update(ingest_jobs)
                .where(ingest_jobs.c.id == job_id)
                .values(
                    documents_done=ingest_jobs.c.documents_done + 1,
                    chunks_written=ingest_jobs.c.chunks_written + written,
                )
            )
    final_status = "failed" if errors else "succeeded"
    with engine.begin() as connection:
        connection.execute(
            update(ingest_jobs)
            .where(ingest_jobs.c.id == job_id)
            .values(status=final_status, error="; ".join(errors)[:4000] or None, finished_at=_now())
        )
        chunks_written = connection.execute(
            select(ingest_jobs.c.chunks_written).where(ingest_jobs.c.id == job_id)
        ).scalar_one()
    _logger.info("job_finished", job_id=str(job_id), status=final_status, chunks_written=chunks_written)
    return final_status
