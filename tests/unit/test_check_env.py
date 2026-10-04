"""check-env reports names only and flags missing values."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.check_env import REQUIRED, main, parse_env_names, report


def test_parse_ignores_comments_and_inline_comments() -> None:
    """Comments, blanks and inline comments are handled."""
    names = parse_env_names("# c\nA=1\nB=\nC=   # just a comment\nexport D=x\n")
    assert names == {"A": True, "B": False, "C": False, "D": True}


def test_report_counts_missing() -> None:
    """Missing and empty variables are both counted."""
    lines, missing_count = report({"FOUNDRY_ENDPOINT": True})
    assert missing_count == len(REQUIRED) - 1
    assert "  [set] FOUNDRY_ENDPOINT" in lines


def test_main_never_prints_values(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Values never reach stdout."""
    secret_value = "super-secret-value-123"
    env_file = tmp_path / ".env"
    env_file.write_text("\n".join(f"{name}={secret_value}" for name in REQUIRED), encoding="utf-8")
    assert main(str(env_file)) == 0
    assert secret_value not in capsys.readouterr().out


def test_main_missing_file(tmp_path: Path) -> None:
    """A missing .env is a failure."""
    assert main(str(tmp_path / "nope.env")) == 1
