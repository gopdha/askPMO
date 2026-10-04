"""api: health, readiness and profiles with fake adapters."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from pmo_core.container import Container
from pmo_core.settings import Settings, load_all_profiles
from tests.fakes import FakeIndex, FakeStorage


def _container(index_reachable: bool = True, foundry_ok: bool = True) -> Container:
    """Build a container of fakes; Foundry is replaced by an injected check."""
    storage = FakeStorage()
    container = Container(
        settings=Settings(foundry_endpoint="", foundry_api_key=""),
        index=FakeIndex(reachable=index_reachable),
        blobs=storage,
        queue=storage,
        engine=None,
        profiles=load_all_profiles(),
    )

    def foundry_check() -> None:
        """Simulated Foundry reachability."""
        if not foundry_ok:
            raise ConnectionError("foundry down")

    container.extra_checks["foundry"] = foundry_check
    return container


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A client against an app wired with healthy fakes."""
    with TestClient(create_app(lambda: _container(), run_bootstrap=False)) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    """Liveness is always 200."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_ok(client: TestClient) -> None:
    """All dependencies reachable gives 200."""
    response = client.get("/api/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True
    assert set(response.json()["checks"]) == {"index", "queue", "foundry"}


@pytest.mark.parametrize(
    ("index_ok", "foundry_ok", "failing"), [(False, True, "index"), (True, False, "foundry")]
)
def test_ready_503(index_ok: bool, foundry_ok: bool, failing: str) -> None:
    """Any unreachable dependency gives 503 and names it."""
    app = create_app(lambda: _container(index_ok, foundry_ok), run_bootstrap=False)
    with TestClient(app) as test_client:
        response = test_client.get("/api/ready")
    assert response.status_code == 503
    assert response.json()["checks"][failing]["ok"] is False


def test_profiles(client: TestClient) -> None:
    """Four profiles with resolved toggles."""
    response = client.get("/api/profiles")
    assert response.status_code == 200
    by_name = {item["name"]: item["toggles"] for item in response.json()}
    assert set(by_name) == {"baseline", "hybrid", "rerank", "full"}
    assert by_name["baseline"]["hybrid"] is False


def test_errors_are_problem_json(client: TestClient) -> None:
    """Unknown routes render RFC 7807."""
    response = client.get("/api/nope")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["status"] == 404
