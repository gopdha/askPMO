"""Environment settings and YAML pipeline profiles.

Environment variables describe *where* things are; profiles describe *how* the pipeline behaves.
Both are validated at load time so a bad value fails fast.
"""

from __future__ import annotations

import hashlib
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROFILE_NAMES: tuple[str, ...] = ("baseline", "hybrid", "rerank", "full")
BASE_PROFILE = "full"
TOGGLE_NAMES: tuple[str, ...] = ("rewrite", "filter", "hybrid", "rerank", "guardrail")


def find_config_dir() -> Path:
    """Locate the `config/` directory.

    Uses `CONFIG_DIR` when set, otherwise walks up from this file and from the current directory.
    """
    configured = os.environ.get("CONFIG_DIR")
    if configured:
        return Path(configured)
    for start in (Path.cwd(), Path(__file__).resolve()):
        for candidate_parent in (start, *start.parents):
            candidate = candidate_parent / "config" / "profiles"
            if candidate.is_dir():
                return candidate.parent
    raise FileNotFoundError("config/profiles not found; set CONFIG_DIR")


class Settings(BaseSettings):
    """Process-wide settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore", case_sensitive=False)

    app_env: Literal["local", "azure"] = "local"
    auth_mode: Literal["none", "platform"] = "none"
    index_backend: Literal["qdrant", "aisearch"] = "qdrant"
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "pmo_chunks"
    storage_connection_string: str = ""
    storage_account_url: str = ""
    blob_container: str = "pmo"
    ingest_queue: str = "ingest-jobs"
    database_url: str = "postgresql+psycopg://pmo:pmo@postgres:5432/pmo"

    foundry_endpoint: str = ""
    foundry_api_key: str = ""
    foundry_api_version: str = "2024-10-21"
    chat_provider: Literal["azure_openai", "azure_ai_inference"] = "azure_openai"
    chat_deployment: str = "gpt-5-mini"
    judge_deployment: str = "gpt-5-mini"
    embedding_deployment: str = "text-embedding-3-small"
    embedding_dimensions: int = Field(default=1536, gt=0)

    arize_space_id: str = ""
    arize_api_key: str = ""
    arize_project_name: str = "askpmo-local"

    default_profile: Literal["baseline", "hybrid", "rerank", "full"] = "full"
    reranker_model: str = "BAAI/bge-reranker-base"
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached process settings."""
    return Settings()


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RewriteConfig(_Strict):
    """Rewrite stage parameters."""

    enabled: bool
    history_turns: int = Field(ge=0)
    expansion: Literal["none", "multi_query", "hyde"]


class FilterConfig(_Strict):
    """Filter stage parameters."""

    enabled: bool


class RetrieveWeights(_Strict):
    """Weighted-RRF leg weights."""

    dense: float = Field(ge=0)
    keyword: float = Field(ge=0)


class RetrieveConfig(_Strict):
    """Retrieve stage parameters."""

    hybrid: bool
    k_candidates: int = Field(gt=0)
    rrf_k: int = Field(gt=0)
    weights: RetrieveWeights
    id_keyword_weight: float = Field(ge=0, le=1)


class RerankConfig(_Strict):
    """Rerank stage parameters."""

    enabled: bool
    top_n: int = Field(gt=0)
    recency_boost: float = Field(ge=0)
    batch_size: int = Field(gt=0)


class GuardrailConfig(_Strict):
    """Guardrail stage parameters."""

    enabled: bool
    threshold: float = Field(ge=0, le=1)


class GenerateConfig(_Strict):
    """Generation parameters."""

    max_context_tokens: int = Field(gt=0)
    temperature: float = Field(ge=0)
    max_output_tokens: int = Field(gt=0)


class Profile(_Strict):
    """A fully resolved pipeline profile."""

    name: str
    rewrite: RewriteConfig
    filter: FilterConfig
    retrieve: RetrieveConfig
    rerank: RerankConfig
    guardrail: GuardrailConfig
    generate: GenerateConfig

    def toggles(self) -> dict[str, bool]:
        """Return the five on/off switches the UI and API expose."""
        return {
            "rewrite": self.rewrite.enabled,
            "filter": self.filter.enabled,
            "hybrid": self.retrieve.hybrid,
            "rerank": self.rerank.enabled,
            "guardrail": self.guardrail.enabled,
        }

    def with_overrides(self, overrides: dict[str, bool | None]) -> Profile:
        """Return a copy with toggle overrides applied; only boolean flags may change."""
        unknown_toggles = set(overrides) - set(TOGGLE_NAMES)
        if unknown_toggles:
            raise ValueError(f"Unknown toggles: {sorted(unknown_toggles)}")
        data = self.model_dump()
        for toggle_name, toggle_value in overrides.items():
            if toggle_value is None:
                continue
            if toggle_name == "hybrid":
                data["retrieve"]["hybrid"] = toggle_value
            else:
                data[toggle_name]["enabled"] = toggle_value
        return Profile.model_validate(data)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge `override` into a copy of `base`."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read_yaml(path: Path) -> dict[str, Any]:
    """Read a YAML mapping from disk."""
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a mapping")
    return loaded


def load_profile(name: str, config_dir: Path | None = None) -> Profile:
    """Load a profile by name; non-base profiles are deep-merged over `full.yaml`."""
    if name not in PROFILE_NAMES:
        raise ValueError(f"Unknown profile {name!r}; expected one of {PROFILE_NAMES}")
    profiles_dir = (config_dir or find_config_dir()) / "profiles"
    base = _read_yaml(profiles_dir / f"{BASE_PROFILE}.yaml")
    data = base if name == BASE_PROFILE else _deep_merge(base, _read_yaml(profiles_dir / f"{name}.yaml"))
    data["name"] = name
    return Profile.model_validate(data)


def load_all_profiles(config_dir: Path | None = None) -> dict[str, Profile]:
    """Load every known profile."""
    return {name: load_profile(name, config_dir) for name in PROFILE_NAMES}


def config_hash(config_dir: Path | None = None) -> str:
    """Hash every profile and prompt file so config changes show up in eval run metadata."""
    root = config_dir or find_config_dir()
    digest = hashlib.sha256()
    for path in sorted([*root.glob("profiles/*.yaml"), *root.glob("prompts/*.md")]):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]
