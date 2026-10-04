"""Chunkers: header paths, tables kept whole, RAID row text, PDF tables, contextual header."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from pmo_core.ingest.chunkers import (
    CHUNK_SIZE,
    MAX_TABLE_CHARS,
    build_chunks,
    csv_drafts,
    markdown_drafts,
    pack_section,
    pdf_drafts,
    raid_row_text,
    split_table,
    table_to_markdown,
)
from pmo_core.ingest.loaders import PdfPage, load
from pmo_core.ingest.metadata import DocumentMetadata, item_ids
from pmo_core.ingest.pipeline import chunk_document
from tests.conftest import REPO_ROOT

CORPUS = REPO_ROOT / "corpus"
META = DocumentMetadata(doc_type="charter", doc_date=date(2026, 1, 14), week=None, title="Charter")


def _table(rows: int, cell: str = "value") -> str:
    """A Markdown table with a header and `rows` body rows."""
    lines = ["| A | B |", "|---|---|"] + [f"| {cell}{index} | {cell} |" for index in range(rows)]
    return "\n".join(lines)


def test_header_path_sections() -> None:
    """Sections are the H2 > H3 path; content before the first H2 is `Overview`."""
    text = (
        "# Title\n\nIntro line.\n\n## Scope\n\nScope text.\n\n"
        "### In scope\n\nItems.\n\n## Risks\n\nRisk text."
    )
    sections = [draft.section for draft in markdown_drafts(text)]
    assert sections == ["Overview", "Scope", "Scope > In scope", "Risks"]


def test_small_table_stays_whole_in_long_section() -> None:
    """A table under 2,400 chars is never split, even when the section exceeds 1,200 chars."""
    table = _table(70)
    assert CHUNK_SIZE < len(table) < MAX_TABLE_CHARS
    body = "Prose. " * 100 + "\n\n" + table + "\n\n" + "More prose. " * 100
    pieces = pack_section(body)
    assert any(table in piece for piece in pieces)
    assert all(len(piece) <= CHUNK_SIZE or piece == table for piece in pieces)


def test_large_table_split_with_header_repeated() -> None:
    """Tables over 2,400 chars are split by rows, each piece repeating the header and separator."""
    pieces = split_table(_table(150))
    assert len(pieces) > 1
    for piece in pieces:
        assert piece.startswith("| A | B |\n|---|---|")
        assert len(piece) <= MAX_TABLE_CHARS
    body_rows = sum(len(piece.split("\n")) - 2 for piece in pieces)
    assert body_rows == 150


def test_long_prose_split_with_overlap() -> None:
    """Prose sections are split near 1,200 chars."""
    body = "\n\n".join(f"Paragraph {index} " + "word " * 60 for index in range(10))
    pieces = pack_section(body)
    assert len(pieces) >= 3
    assert all(len(piece) <= CHUNK_SIZE for piece in pieces)


def test_raid_row_text_labels() -> None:
    """RAID rows render as labeled text in the LLD order."""
    row = {
        "ID": "RSK-014",
        "Type": "Risk",
        "Title": "Connector slip",
        "Description": "Late.",
        "Workstream": "WS2",
        "Owner": "Marcus Chen",
        "Severity": "High",
        "Status": "Open",
        "Date Raised": "2026-03-02",
        "Date Closed": "",
        "Mitigation / Resolution": "Weekly call.",
        "Linked Items": "ISS-009",
    }
    assert raid_row_text(row) == (
        "RAID item RSK-014 (Risk) | Title: Connector slip | Workstream: WS2 | Owner: Marcus Chen | "
        "Severity: High | Status: Open | Raised: 2026-03-02 | Description: Late. | "
        "Mitigation / Resolution: Weekly call. | Linked: ISS-009"
    )


def test_csv_one_chunk_per_row() -> None:
    """The RAID log produces one chunk per row with the item ID as section."""
    loaded = load("raid.csv", (CORPUS / "03_raid" / "raid_log_2026-04-03.csv").read_bytes())
    drafts = csv_drafts(loaded.rows)
    assert len(drafts) == len(loaded.rows) == 18
    assert all(draft.body.startswith(f"RAID item {draft.section} (") for draft in drafts)


def test_pdf_tables_are_own_chunks() -> None:
    """PDF tables become Markdown tables, separate from page text, sectioned by page."""
    page = PdfPage(number=3, text="Some page text.", tables=[[["H1", "H2"], ["a", "b"]]])
    drafts = pdf_drafts([page])
    assert [draft.section for draft in drafts] == ["page 3", "page 3"]
    assert (
        drafts[1].body == table_to_markdown([["H1", "H2"], ["a", "b"]]) == "| H1 | H2 |\n|---|---|\n| a | b |"
    )


def test_build_chunks_header_ids_and_chunk_ids() -> None:
    """Every chunk starts with `[title — section]`, carries its IDs and a `{doc}:{n}` ID."""
    drafts = markdown_drafts("# Charter\n\n## Risks\n\nSee RSK-014 and CR-007.")
    chunks = build_chunks("doc-1", "charter.md", META, drafts)
    assert chunks[0].chunk_id == "doc-1:0"
    assert chunks[0].text.startswith("[Charter — Risks]\n")
    assert chunks[0].ids == ("RSK-014", "CR-007")
    assert chunks[0].doc_date == date(2026, 1, 14)


@pytest.mark.parametrize("path", sorted(p for p in CORPUS.rglob("*") if p.is_file()), ids=lambda p: p.name)
def test_corpus_chunks_well_formed(path: Path) -> None:
    """Every corpus document chunks into bounded, headed chunks with correct IDs."""
    rel_path = path.relative_to(CORPUS).as_posix()
    processed = chunk_document("doc", rel_path, path.read_bytes())
    assert processed.chunks
    for chunk in processed.chunks:
        assert chunk.text.startswith(f"[{processed.metadata.title} — {chunk.section}]\n")
        assert len(chunk.text) <= MAX_TABLE_CHARS + 200
        assert chunk.ids == item_ids(chunk.text)
        assert "�" not in chunk.text


def test_corpus_chunk_count_is_logged() -> None:
    """Offline chunk count for the whole corpus (the seed gate asserts the live count)."""
    total = sum(
        len(chunk_document("doc", path.relative_to(CORPUS).as_posix(), path.read_bytes()).chunks)
        for path in CORPUS.rglob("*")
        if path.is_file()
    )
    print(f"corpus chunk count: {total}")
    assert total > 150
