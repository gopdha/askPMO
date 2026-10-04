"""Ingestion pipeline: load → metadata → chunk → embed → index."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import partial
from pathlib import PurePosixPath
from typing import TypeVar

import structlog

from pmo_core.adapters.base import Embedder, IndexBackend
from pmo_core.ingest.chunkers import build_chunks, csv_drafts, markdown_drafts, pdf_drafts
from pmo_core.ingest.loaders import load
from pmo_core.ingest.metadata import DocumentMetadata, extract_metadata
from pmo_core.models import Chunk

EMBED_BATCH_SIZE = 64
EMBED_ATTEMPTS = 4
_logger = structlog.get_logger(__name__)
T = TypeVar("T")


@dataclass(frozen=True)
class ProcessedDocument:
    """Metadata and chunks for one document."""

    metadata: DocumentMetadata
    chunks: list[Chunk]


def content_hash(data: bytes) -> str:
    """SHA-256 of the raw bytes; used to skip unchanged re-uploads."""
    return hashlib.sha256(data).hexdigest()


def chunk_document(document_id: str, rel_path: str, data: bytes) -> ProcessedDocument:
    """Load a document and turn it into chunks with metadata (pure; no I/O)."""
    filename = PurePosixPath(rel_path.replace("\\", "/")).name
    loaded = load(filename, data)
    metadata = extract_metadata(rel_path, loaded.text)
    if loaded.kind == "csv":
        drafts = csv_drafts(loaded.rows)
    elif loaded.kind == "pdf":
        drafts = pdf_drafts(loaded.pages)
    else:
        drafts = markdown_drafts(loaded.text)
    return ProcessedDocument(metadata, build_chunks(document_id, filename, metadata, drafts))


def with_retries(call: Callable[[], T], attempts: int = EMBED_ATTEMPTS, base_delay_s: float = 1.0) -> T:
    """Run `call`, retrying with exponential backoff."""
    for attempt in range(1, attempts + 1):
        try:
            return call()
        except Exception as exc:
            if attempt == attempts:
                raise
            _logger.warning("retrying", attempt=attempt, error_type=type(exc).__name__)
            time.sleep(base_delay_s * 2 ** (attempt - 1))
    raise AssertionError("unreachable")


def embed_chunks(
    embedder: Embedder, chunks: Sequence[Chunk], batch_size: int = EMBED_BATCH_SIZE
) -> list[list[float]]:
    """Embed chunk texts in batches, retrying each batch."""
    vectors: list[list[float]] = []
    for start in range(0, len(chunks), batch_size):
        texts = [chunk.text for chunk in chunks[start : start + batch_size]]
        vectors.extend(with_retries(partial(embedder.embed_documents, texts)))
    return vectors


def index_document(
    index: IndexBackend, embedder: Embedder, processed: ProcessedDocument, document_id: str
) -> int:
    """Replace a document's chunks in the index; returns the number written."""
    vectors = embed_chunks(embedder, processed.chunks)
    index.delete_document(document_id)
    if processed.chunks:
        index.upsert(processed.chunks, vectors)
    return len(processed.chunks)
