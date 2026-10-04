"""Profiles: loading, inheritance from full.yaml, toggle overrides, config hash."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pmo_core.settings import Settings, config_hash, load_all_profiles, load_profile

ALL_TOGGLES = ("rewrite", "filter", "hybrid", "rerank", "guardrail")


def test_full_profile_matches_lld() -> None:
    """full.yaml holds the LLD defaults."""
    profile = load_profile("full")
    assert profile.toggles() == dict.fromkeys(ALL_TOGGLES, True)
    assert profile.retrieve.k_candidates == 30
    assert profile.retrieve.rrf_k == 60
    assert profile.retrieve.id_keyword_weight == 0.7
    assert profile.rerank.top_n == 5
    assert profile.guardrail.threshold == 0.20
    assert profile.generate.max_context_tokens == 3000


@pytest.mark.parametrize(
    ("name", "enabled"),
    [
        ("baseline", set()),
        ("hybrid", {"hybrid"}),
        ("rerank", {"hybrid", "rerank"}),
    ],
)
def test_derived_profiles_toggles(name: str, enabled: set[str]) -> None:
    """Derived profiles override only their toggles and inherit numeric parameters."""
    profile = load_profile(name)
    assert profile.name == name
    assert profile.toggles() == {toggle: toggle in enabled for toggle in ALL_TOGGLES}
    assert profile.rerank.top_n == 5
    assert profile.retrieve.k_candidates == 30


def test_rerank_profile_has_no_recency_boost() -> None:
    """The rerank profile turns recency off."""
    assert load_profile("rerank").rerank.recency_boost == 0.0


def test_overrides_flip_only_flags() -> None:
    """Per-request overrides flip enabled/hybrid flags; None leaves the profile value."""
    profile = load_profile("full").with_overrides({"rerank": False, "hybrid": False, "rewrite": None})
    assert profile.rerank.enabled is False
    assert profile.retrieve.hybrid is False
    assert profile.rewrite.enabled is True
    assert profile.rerank.top_n == 5


def test_unknown_override_rejected() -> None:
    """Overrides cannot touch numeric parameters."""
    with pytest.raises(ValueError, match="Unknown toggles"):
        load_profile("full").with_overrides({"top_n": True})


def test_unknown_profile_rejected() -> None:
    """Only the four profiles exist."""
    with pytest.raises(ValueError, match="Unknown profile"):
        load_profile("turbo")


def test_all_profiles_and_hash_stable() -> None:
    """Every profile loads and the config hash is deterministic."""
    assert set(load_all_profiles()) == {"baseline", "hybrid", "rerank", "full"}
    assert config_hash() == config_hash()
    assert len(config_hash()) == 16


def test_settings_validate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bad values fail fast."""
    monkeypatch.setenv("EMBEDDING_DIMENSIONS", "0")
    with pytest.raises(ValidationError):
        Settings()
    monkeypatch.setenv("EMBEDDING_DIMENSIONS", "1536")
    monkeypatch.setenv("INDEX_BACKEND", "elastic")
    with pytest.raises(ValidationError):
        Settings()
