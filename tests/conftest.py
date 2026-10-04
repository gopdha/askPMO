"""Shared fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _config_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the profile loader at the repo's config directory."""
    monkeypatch.setenv("CONFIG_DIR", str(REPO_ROOT / "config"))
