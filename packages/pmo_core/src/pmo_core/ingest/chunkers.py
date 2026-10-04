"""Chunking per format. Every chunk's text starts with `[{title} — {section}]`."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from pmo_core.ingest.loaders import PdfPage
from pmo_core.ingest.metadata import DocumentMetadata, item_ids
from pmo_core.models import Chunk

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
MAX_TABLE_CHARS = 2400
OVERVIEW_SECTION = "Overview"
HEADER_LEVELS = [("#", "h1"), ("##", "h2"), ("###", "h3")]
CSV_FIELDS: tuple[tuple[str, str], ...] = (
    ("Title", "Title"),
    ("Workstream", "Workstream"),
    ("Owner", "Owner"),
    ("Severity", "Severity"),
    ("Status", "Status"),
    ("Date Raised", "Raised"),
    ("Date Closed", "Closed"),
    ("Description", "Description"),
    ("Mitigation / Resolution", "Mitigation / Resolution"),
    ("Linked Items", "Linked"),
)

_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, separators=["\n\n", "\n", " "]
)


@dataclass(frozen=True)
class ChunkDraft:
    """Chunk body and section before the contextual header and IDs are added."""

    section: str
    body: str


def _is_table_line(line: str) -> bool:
    """A Markdown table row."""
    return line.lstrip().startswith("|")


def split_table(table: str, max_chars: int = MAX_TABLE_CHARS) -> list[str]:
    """Keep a table whole when small; otherwise split by rows, repeating the header and separator."""
    if len(table) <= max_chars:
        return [table]
    lines = table.split("\n")
    header = (
        lines[:2] if len(lines) > 1 and set(lines[1].replace("|", "").strip()) <= set("-: ") else lines[:1]
    )
    pieces: list[str] = []
    current = list(header)
    for row in lines[len(header) :]:
        if len("\n".join([*current, row])) > max_chars and len(current) > len(header):
            pieces.append("\n".join(current))
            current = list(header)
        current.append(row)
    if len(current) > len(header):
        pieces.append("\n".join(current))
    return pieces


def _units(body: str) -> list[tuple[str, bool]]:
    """Split a section into (text, is_atomic) units: tables are atomic, prose is split at 1,200 chars."""
    units: list[tuple[str, bool]] = []
    block: list[str] = []
    block_is_table = False

    def flush() -> None:
        """Emit the block collected so far."""
        text = "\n".join(block).strip()
        if not text:
            return
        if block_is_table:
            units.extend((piece, True) for piece in split_table(text))
        else:
            units.extend((piece, False) for piece in _text_splitter.split_text(text))

    for line in body.split("\n"):
        line_is_table = _is_table_line(line)
        if block and line_is_table != block_is_table and line.strip():
            flush()
            block = []
        if line.strip() or block:
            block_is_table = line_is_table if line.strip() else block_is_table
            block.append(line.rstrip())
    flush()
    return units


def pack_section(body: str) -> list[str]:
    """Greedily pack units into chunks of at most 1,200 chars; a larger table stays whole on its own."""
    if len(body.strip()) <= CHUNK_SIZE:
        return [body.strip()] if body.strip() else []
    packed: list[str] = []
    current = ""
    for text, _ in _units(body):
        candidate = f"{current}\n\n{text}" if current else text
        if len(candidate) <= CHUNK_SIZE:
            current = candidate
            continue
        if current:
            packed.append(current)
        current = text
    if current:
        packed.append(current)
    return packed


def markdown_drafts(text: str) -> list[ChunkDraft]:
    """Header split on levels 1–3, then size-bounded packing within each section."""
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=HEADER_LEVELS, strip_headers=True)
    drafts: list[ChunkDraft] = []
    for document in splitter.split_text(text):
        path = [document.metadata[key] for key in ("h2", "h3") if document.metadata.get(key)]
        section = " > ".join(path) if path else OVERVIEW_SECTION
        body = "\n".join(line.rstrip() for line in document.page_content.split("\n"))
        drafts.extend(ChunkDraft(section, piece) for piece in pack_section(body))
    return drafts


def raid_row_text(row: dict[str, str]) -> str:
    """Render one RAID row as labeled text."""
    parts = [f"RAID item {row.get('ID', '')} ({row.get('Type', '')})"]
    parts.extend(f"{label}: {row[key]}" for key, label in CSV_FIELDS if row.get(key))
    return " | ".join(parts)


def csv_drafts(rows: Sequence[dict[str, str]]) -> list[ChunkDraft]:
    """One chunk per RAID row; the section is the item ID."""
    return [
        ChunkDraft(row.get("ID") or f"row {number}", raid_row_text(row)) for number, row in enumerate(rows, 1)
    ]


def table_to_markdown(table: list[list[str]]) -> str:
    """Render a cell grid as a Markdown table (first row is the header)."""
    width = max(len(row) for row in table)
    padded = [row + [""] * (width - len(row)) for row in table]
    lines = ["| " + " | ".join(padded[0]) + " |", "|" + "---|" * width]
    lines.extend("| " + " | ".join(row) + " |" for row in padded[1:])
    return "\n".join(lines)


def pdf_drafts(pages: Sequence[PdfPage]) -> list[ChunkDraft]:
    """Per page: each table is its own chunk (split by rows if large); the rest is chunked like prose."""
    drafts: list[ChunkDraft] = []
    for page in pages:
        section = f"page {page.number}"
        if page.text.strip():
            drafts.extend(
                ChunkDraft(section, piece) for piece in _text_splitter.split_text(page.text.strip())
            )
        for table in page.tables:
            drafts.extend(ChunkDraft(section, piece) for piece in split_table(table_to_markdown(table)))
    return drafts


def build_chunks(
    document_id: str, source: str, metadata: DocumentMetadata, drafts: Sequence[ChunkDraft]
) -> list[Chunk]:
    """Add the contextual header, chunk IDs and item IDs."""
    chunks: list[Chunk] = []
    for chunk_no, draft in enumerate(drafts):
        text = f"[{metadata.title} — {draft.section}]\n{draft.body}"
        chunks.append(
            Chunk(
                chunk_id=f"{document_id}:{chunk_no}",
                document_id=document_id,
                text=text,
                source=source,
                section=draft.section,
                doc_type=metadata.doc_type,
                doc_date=metadata.doc_date,
                week=metadata.week,
                ids=item_ids(text),
            )
        )
    return chunks
