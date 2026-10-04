"""Deterministic document metadata from the relative path, the filename and the first lines of text."""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date
from pathlib import PurePosixPath

ITEM_ID_RE = re.compile(r"\b(?:RSK|ISS|ACT|DEC|CR)-\d{3}\b")
WEEK_RE = re.compile(r"_wk(\d{2})_")
FULL_DATE_RE = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
# A YYYY-MM month that is not part of a longer identifier (e.g. not the "2026-01" in "NRG-COB-2026-01").
MONTH_IN_FILENAME_RE = re.compile(r"(?<![A-Za-z0-9-])(\d{4})-(\d{2})(?![-\d])")
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
TEXT_DATE_WINDOW = 600

FOLDER_DOC_TYPES: dict[str, str] = {
    "02": "status_report",
    "03": "raid_log",
    "05": "meeting_minutes",
    "07": "reference",
}
# Folders 01, 04 and 06 are typed by filename; first matching pattern wins.
FILENAME_DOC_TYPES: tuple[tuple[str, str], ...] = (
    ("charter", "charter"),
    ("sow", "sow"),
    ("cutover_strategy", "cutover_strategy"),
    ("change_log", "change_log"),
    ("cr-", "change_request"),
    ("budget", "budget_report"),
    ("resource_plan", "resource_plan"),
)


@dataclass(frozen=True)
class DocumentMetadata:
    """Document-level metadata stored on the document row and every chunk."""

    doc_type: str
    doc_date: date | None
    week: int | None
    title: str


def doc_type_for(rel_path: str) -> str:
    """Map a relative path to a document type (top folder first, then filename)."""
    path = PurePosixPath(rel_path.replace("\\", "/"))
    folder_prefix = path.parts[0][:2] if len(path.parts) > 1 else ""
    if folder_prefix in FOLDER_DOC_TYPES:
        return FOLDER_DOC_TYPES[folder_prefix]
    if folder_prefix in {"01", "04", "06"}:
        filename = path.name.lower()
        for pattern, doc_type in FILENAME_DOC_TYPES:
            if pattern in filename:
                return doc_type
    return "other"


def _safe_date(year: int, month: int, day: int) -> date | None:
    """Build a date, returning None for impossible values."""
    try:
        return date(year, month, day)
    except ValueError:
        return None


def doc_date_for(filename: str, text: str) -> date | None:
    """First full date in the filename; else month in filename (last day); else first date in text head."""
    full_match = FULL_DATE_RE.search(filename)
    if full_match:
        return _safe_date(*(int(part) for part in full_match.groups()))
    month_match = MONTH_IN_FILENAME_RE.search(filename)
    if month_match:
        year, month = int(month_match.group(1)), int(month_match.group(2))
        if 1 <= month <= 12:
            return date(year, month, calendar.monthrange(year, month)[1])
    text_match = FULL_DATE_RE.search(text[:TEXT_DATE_WINDOW])
    if text_match:
        return _safe_date(*(int(part) for part in text_match.groups()))
    return None


def week_for(filename: str) -> int | None:
    """Status-report week number from `_wkNN_` in the filename."""
    match = WEEK_RE.search(filename)
    return int(match.group(1)) if match else None


def title_for(filename: str, text: str, week: int | None = None) -> str:
    """First Markdown H1, or the filename; weekly reports get "– Week N" so the header names the week."""
    match = H1_RE.search(text)
    title = match.group(1).strip() if match else filename
    return f"{title} – Week {week}" if week is not None else title


def item_ids(text: str) -> tuple[str, ...]:
    """Item IDs (RSK/ISS/ACT/DEC/CR-NNN) in order of first appearance, deduplicated."""
    return tuple(dict.fromkeys(ITEM_ID_RE.findall(text)))


def extract_metadata(rel_path: str, text: str) -> DocumentMetadata:
    """Compute all document-level metadata."""
    filename = PurePosixPath(rel_path.replace("\\", "/")).name
    week = week_for(filename)
    return DocumentMetadata(
        doc_type=doc_type_for(rel_path),
        doc_date=doc_date_for(filename, text),
        week=week,
        title=title_for(filename, text, week),
    )
