"""Document upload, listing, ingest job progress and chunk lookup."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select

from api.deps import get_container
from api.schemas import ChunkOut, DocumentOut, IngestJobOut, UploadResponse
from pmo_core.container import Container, require_engine
from pmo_core.db.tables import documents, ingest_jobs
from pmo_core.ingest.jobs import UploadedFile, register_upload
from pmo_core.ingest.loaders import kind_for

router = APIRouter(tags=["documents"])
ContainerDep = Annotated[Container, Depends(get_container)]


@router.post("/documents", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_documents(
    container: ContainerDep,
    files: Annotated[list[UploadFile], File(alias="files[]")],
    rel_paths: Annotated[list[str], Form(alias="rel_paths[]")],
) -> UploadResponse:
    """Store files, create one ingest job and enqueue it; unchanged re-uploads are skipped."""
    if len(files) != len(rel_paths):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "files[] and rel_paths[] must have the same length")
    uploads: list[UploadedFile] = []
    for upload, rel_path in zip(files, rel_paths, strict=True):
        try:
            kind_for(rel_path)
        except ValueError as exc:
            raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc)) from exc
        uploads.append(UploadedFile(rel_path=rel_path, data=await upload.read()))
    try:
        result = register_upload(require_engine(container), container.blobs, uploads)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    if result.document_ids:
        container.queue.send(str(result.job_id))
    return UploadResponse(job_id=result.job_id, document_ids=result.document_ids)


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(container: ContainerDep) -> list[DocumentOut]:
    """All documents ordered by relative path."""
    with require_engine(container).connect() as connection:
        rows = connection.execute(select(documents).order_by(documents.c.rel_path)).mappings().all()
    return [DocumentOut.model_validate(dict(row)) for row in rows]


@router.get("/ingest-jobs/{job_id}", response_model=IngestJobOut)
def get_ingest_job(job_id: uuid.UUID, container: ContainerDep) -> IngestJobOut:
    """Progress of one ingest job."""
    with require_engine(container).connect() as connection:
        row = connection.execute(select(ingest_jobs).where(ingest_jobs.c.id == job_id)).mappings().first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ingest job not found")
    return IngestJobOut.model_validate(dict(row))


@router.get("/chunks/{chunk_id}", response_model=ChunkOut)
def get_chunk(chunk_id: str, container: ContainerDep) -> ChunkOut:
    """Full chunk text and metadata, for a clicked citation."""
    chunk = container.index.get_chunk(chunk_id)
    if chunk is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "chunk not found")
    return ChunkOut(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        text=chunk.text,
        source=chunk.source,
        section=chunk.section,
        doc_type=chunk.doc_type,
        doc_date=chunk.doc_date,
        week=chunk.week,
        ids=list(chunk.ids),
    )
