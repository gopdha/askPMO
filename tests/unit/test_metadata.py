"""Metadata rules (doc_type, doc_date, week, title, IDs) for every corpus file."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from pmo_core.ingest.loaders import load
from pmo_core.ingest.metadata import doc_date_for, doc_type_for, extract_metadata, item_ids, week_for
from tests.conftest import REPO_ROOT

CORPUS = REPO_ROOT / "corpus"

# rel_path -> (doc_type, doc_date, week)
EXPECTED: dict[str, tuple[str, date | None, int | None]] = {
    "01_governance/SOW_NRG-COB-2026-01_project_atlas.pdf": ("sow", date(2026, 1, 9), None),
    "01_governance/cutover_strategy_v2.0.md": ("cutover_strategy", date(2026, 3, 16), None),
    "01_governance/project_atlas_charter_v1.0.md": ("charter", date(2026, 1, 14), None),
    **{
        f"02_status_reports/status_report_wk{week:02d}_{day.isoformat()}.md": ("status_report", day, week)
        for week, day in enumerate(
            [
                date(2026, 1, 16),
                date(2026, 1, 23),
                date(2026, 1, 30),
                date(2026, 2, 6),
                date(2026, 2, 13),
                date(2026, 2, 20),
                date(2026, 2, 27),
                date(2026, 3, 6),
                date(2026, 3, 13),
                date(2026, 3, 20),
                date(2026, 3, 27),
                date(2026, 4, 3),
            ],
            start=1,
        )
    },
    "03_raid/raid_log_2026-04-03.csv": ("raid_log", date(2026, 4, 3), None),
    "04_change_requests/CR-003_store_inventory_api.md": ("change_request", date(2026, 2, 4), None),
    "04_change_requests/CR-005_disaster_recovery_region.md": ("change_request", date(2026, 2, 13), None),
    "04_change_requests/CR-007_go_live_replan.md": ("change_request", date(2026, 2, 27), None),
    "04_change_requests/CR-008_loyalty_module.md": ("change_request", date(2026, 3, 16), None),
    "04_change_requests/change_log.md": ("change_log", date(2026, 3, 27), None),
    "05_meeting_minutes/2026-01-28_steerco_SC-01.md": ("meeting_minutes", date(2026, 1, 28), None),
    "05_meeting_minutes/2026-02-18_data_migration_deep_dive.md": ("meeting_minutes", date(2026, 2, 18), None),
    "05_meeting_minutes/2026-02-25_steerco_SC-02.md": ("meeting_minutes", date(2026, 2, 25), None),
    "05_meeting_minutes/2026-03-04_steerco_SC-03_special.md": ("meeting_minutes", date(2026, 3, 4), None),
    "05_meeting_minutes/2026-03-11_databridge_vendor_review.md": ("meeting_minutes", date(2026, 3, 11), None),
    "05_meeting_minutes/2026-03-18_integration_sync.md": ("meeting_minutes", date(2026, 3, 18), None),
    "05_meeting_minutes/2026-03-25_steerco_SC-04.md": ("meeting_minutes", date(2026, 3, 25), None),
    "06_finance_resourcing/budget_burn_report_2026-03.pdf": ("budget_report", date(2026, 3, 31), None),
    "06_finance_resourcing/resource_plan_v3.0.pdf": ("resource_plan", date(2026, 4, 1), None),
    "07_reference/project_helios_lessons_learned_2024.md": ("reference", date(2024, 12, 12), None),
}


def test_expected_table_covers_whole_corpus() -> None:
    """Every corpus file (31) has an expectation, and vice versa."""
    on_disk = {path.relative_to(CORPUS).as_posix() for path in CORPUS.rglob("*") if path.is_file()}
    assert len(on_disk) == 31
    assert on_disk == set(EXPECTED)


@pytest.mark.parametrize("rel_path", sorted(EXPECTED))
def test_metadata_for_corpus_file(rel_path: str) -> None:
    """doc_type, doc_date and week follow the LLD rules for this file."""
    loaded = load(Path(rel_path).name, (CORPUS / rel_path).read_bytes())
    metadata = extract_metadata(rel_path, loaded.text)
    assert (metadata.doc_type, metadata.doc_date, metadata.week) == EXPECTED[rel_path]


def test_title_from_h1_and_week_suffix() -> None:
    """Title is the first H1; weekly reports name their week."""
    rel_path = "02_status_reports/status_report_wk06_2026-02-20.md"
    loaded = load("x.md", (CORPUS / rel_path).read_bytes())
    assert extract_metadata(rel_path, loaded.text).title == "Project Atlas – Weekly Status Report – Week 6"
    assert extract_metadata("01_governance/x.md", "# Charter\n\ntext").title == "Charter"
    assert extract_metadata("03_raid/raid.csv", "ID,Type").title == "raid.csv"


@pytest.mark.parametrize(
    ("filename", "text", "expected"),
    [
        ("status_report_wk06_2026-02-20.md", "", date(2026, 2, 20)),
        ("budget_burn_report_2026-03.pdf", "Data as of 2026-03-15", date(2026, 3, 31)),
        ("report_2024-02.md", "", date(2024, 2, 29)),
        ("SOW_NRG-COB-2026-01_x.pdf", "Effective date: 2026-01-09", date(2026, 1, 9)),
        ("charter.md", "x" * 700 + "2026-01-14", None),
        ("charter.md", "Approved 2026-01-14 then 2026-02-01", date(2026, 1, 14)),
    ],
)
def test_doc_date_rules(filename: str, text: str, expected: date | None) -> None:
    """Filename full date, then filename month (last day, not inside an ID), then text head (600 chars)."""
    assert doc_date_for(filename, text) == expected


def test_doc_type_fallbacks() -> None:
    """Unknown folders and filenames map to `other`."""
    assert doc_type_for("08_misc/notes.md") == "other"
    assert doc_type_for("01_governance/random.md") == "other"
    assert doc_type_for("notes.md") == "other"


def test_week_and_ids() -> None:
    """Week from `_wkNN_`; IDs deduplicated in order; partial IDs ignored."""
    assert week_for("status_report_wk11_2026-03-27.md") == 11
    assert week_for("weekly.md") is None
    assert item_ids("RSK-014 and CR-007, again RSK-014; ISS-0091 XRSK-001 DEC-002") == (
        "RSK-014",
        "CR-007",
        "DEC-002",
    )
