"""Throwaway Qdrant and Postgres containers for contract tests (skipped when Docker is unavailable)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

QDRANT_IMAGE = "qdrant/qdrant:v1.19.1"
POSTGRES_IMAGE = "postgres:16.15-bookworm"


def _docker_available() -> bool:
    """True when a Docker daemon answers."""
    try:
        import docker

        docker.from_env().ping()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def qdrant_url() -> Iterator[str]:
    """URL of a fresh Qdrant container."""
    if not _docker_available():
        pytest.skip("Docker not available")
    from testcontainers.core.container import DockerContainer
    from testcontainers.core.wait_strategies import HttpWaitStrategy

    container = DockerContainer(QDRANT_IMAGE).with_exposed_ports(6333)
    container.waiting_for(HttpWaitStrategy(6333, "/readyz"))
    with container:
        yield f"http://{container.get_container_host_ip()}:{container.get_exposed_port(6333)}"


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    """SQLAlchemy URL of a fresh, migrated Postgres container."""
    if not _docker_available():
        pytest.skip("Docker not available")
    from testcontainers.postgres import PostgresContainer

    from pmo_core.db import run_migrations

    with PostgresContainer(
        POSTGRES_IMAGE, username="pmo", password="pmo", dbname="pmo", driver="psycopg"
    ) as pg:
        url = pg.get_connection_url()
        run_migrations(url)
        yield url
