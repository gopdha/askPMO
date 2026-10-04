"""Format loaders: turn raw bytes into text blocks that the chunkers understand."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from pathlib import PurePosixPath

import pdfplumber

# The corpus PDFs render en dashes with a glyph that has no Unicode mapping.
REPLACEMENT_CHAR = "�"
EN_DASH = "–"


@dataclass(frozen=True)
class PdfPage:
    """One PDF page: free text outside tables, plus each table as rows of cells."""

    number: int
    text: str
    tables: list[list[list[str]]] = field(default_factory=list)


@dataclass(frozen=True)
class LoadedDocument:
    """Extracted content of one document, in exactly one of the three shapes."""

    kind: str  # markdown | csv | pdf
    text: str  # full text (used for metadata and hashing-independent checks)
    rows: list[dict[str, str]] = field(default_factory=list)
    pages: list[PdfPage] = field(default_factory=list)


def kind_for(filename: str) -> str:
    """Pick the loader from the file extension."""
    suffix = PurePosixPath(filename).suffix.lower()
    if suffix in {".md", ".markdown", ".txt"}:
        return "markdown"
    if suffix == ".csv":
        return "csv"
    if suffix == ".pdf":
        return "pdf"
    raise ValueError(f"Unsupported file type: {suffix or filename}")


def _clean_cell(cell: str | None) -> str:
    """Join wrapped cell lines with spaces and repair unmapped dash glyphs."""
    return " ".join((cell or "").replace(REPLACEMENT_CHAR, EN_DASH).split())


def load_markdown(data: bytes) -> LoadedDocument:
    """Markdown is chunked from its raw text."""
    text = data.decode("utf-8-sig").replace("\r\n", "\n")
    return LoadedDocument(kind="markdown", text=text)


def load_csv(data: bytes) -> LoadedDocument:
    """One dict per CSV row, keyed by header."""
    text = data.decode("utf-8-sig").replace("\r\n", "\n")
    rows = [
        {key.strip(): (value or "").strip() for key, value in row.items()}
        for row in csv.DictReader(io.StringIO(text))
    ]
    return LoadedDocument(kind="csv", text=text, rows=rows)


def load_pdf(data: bytes) -> LoadedDocument:
    """Per page: tables as cell grids, and the remaining text with table regions removed."""
    pages: list[PdfPage] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            found_tables = page.find_tables()
            tables = [
                [[_clean_cell(cell) for cell in row] for row in table.extract()] for table in found_tables
            ]
            remaining = page
            for table in found_tables:
                remaining = remaining.outside_bbox(table.bbox)
            page_text = (remaining.extract_text() or "").replace(REPLACEMENT_CHAR, EN_DASH)
            pages.append(PdfPage(number=page_number, text=page_text, tables=[t for t in tables if t]))
    full_text = "\n".join(page.text for page in pages)
    return LoadedDocument(kind="pdf", text=full_text, pages=pages)


def load(filename: str, data: bytes) -> LoadedDocument:
    """Dispatch to the loader for this file type."""
    loaders = {"markdown": load_markdown, "csv": load_csv, "pdf": load_pdf}
    return loaders[kind_for(filename)](data)
