"""The initial migration contains exactly the LLD tables."""

from __future__ import annotations

import importlib.util
import re

from pmo_core.db import MIGRATIONS_DIR

LLD_TABLES = {
    "documents",
    "ingest_jobs",
    "conversations",
    "turns",
    "turn_stages",
    "feedback",
    "eval_runs",
    "eval_results",
}


def test_initial_migration_tables() -> None:
    """All eight version-1 tables are created in schema app."""
    path = MIGRATIONS_DIR / "versions" / "0001_initial_schema.py"
    spec = importlib.util.spec_from_file_location("m0001", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert set(re.findall(r"CREATE TABLE app\.(\w+)", module.DDL)) == LLD_TABLES
