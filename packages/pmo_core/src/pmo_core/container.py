"""Dependency wiring: adapters built once per process from `Settings`."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import httpx
from sqlalchemy import Engine

from pmo_core import db
from pmo_core.adapters.base import BlobStore, Embedder, IndexBackend, JobQueue
from pmo_core.settings import Profile, Settings, load_all_profiles


@dataclass
class Container:
    """Process-wide adapters. Tests construct it directly with fakes."""

    settings: Settings
    index: IndexBackend
    blobs: BlobStore
    queue: JobQueue
    engine: Engine | None
    profiles: dict[str, Profile]
    embedder: Embedder | None = None
    extra_checks: dict[str, Callable[[], None]] = field(default_factory=dict)

    def readiness(self) -> dict[str, dict[str, Any]]:
        """Check every dependency; each entry is `{"ok": bool, "error": str | None}`."""
        checks: dict[str, Callable[[], None]] = {
            "index": self.index.ping,
            "queue": _ping_of(self.queue),
            "foundry": lambda: check_foundry(self.settings),
        }
        if self.engine is not None:
            engine = self.engine
            checks["database"] = lambda: db.ping(engine)
        checks.update(self.extra_checks)
        results: dict[str, dict[str, Any]] = {}
        for name, check in checks.items():
            try:
                check()
                results[name] = {"ok": True, "error": None}
            except Exception as exc:
                results[name] = {"ok": False, "error": type(exc).__name__ + ": " + str(exc)[:200]}
        return results


def _ping_of(adapter: object) -> Callable[[], None]:
    """Return the adapter's `ping` method, or a no-op when it has none."""
    ping = getattr(adapter, "ping", None)
    return ping if callable(ping) else (lambda: None)


def check_foundry(settings: Settings) -> None:
    """Raise unless the Foundry endpoint is configured and answers HTTP (any status counts as reachable)."""
    if not settings.foundry_endpoint or not settings.foundry_api_key:
        raise RuntimeError("FOUNDRY_ENDPOINT / FOUNDRY_API_KEY not configured")
    httpx.get(settings.foundry_endpoint, timeout=5.0)


def build_container(settings: Settings) -> Container:
    """Build real adapters for the configured environment."""
    from pmo_core.adapters.index_qdrant import QdrantIndex
    from pmo_core.adapters.llm import get_embeddings
    from pmo_core.adapters.storage_azure import AzureStorage

    if settings.index_backend != "qdrant":
        raise NotImplementedError("INDEX_BACKEND=aisearch arrives in P7")
    index = QdrantIndex(settings.qdrant_url, settings.qdrant_collection, settings.embedding_dimensions)
    storage = AzureStorage(
        container=settings.blob_container,
        queue=settings.ingest_queue,
        connection_string=settings.storage_connection_string,
        account_url=settings.storage_account_url,
    )
    return Container(
        settings=settings,
        index=index,
        blobs=storage,
        queue=storage,
        engine=db.make_engine(settings.database_url),
        profiles=load_all_profiles(),
        embedder=get_embeddings(settings),
    )


def bootstrap(container: Container) -> None:
    """Run migrations and create the index, blob container and queue if missing."""
    from pmo_core.adapters.storage_azure import AzureStorage

    db.run_migrations(container.settings.database_url)
    container.index.ensure_schema()
    if isinstance(container.blobs, AzureStorage):
        container.blobs.ensure()


def require_engine(container: Container) -> Engine:
    """Return the database engine or fail clearly."""
    if container.engine is None:
        raise RuntimeError("database not configured")
    return container.engine


def require_embedder(container: Container) -> Embedder:
    """Return the embedder or fail clearly."""
    if container.embedder is None:
        raise RuntimeError("embeddings not configured")
    return container.embedder
