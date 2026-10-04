"""Integration tests against the running Compose stack (through nginx on :8080)."""

from __future__ import annotations

import os

import httpx
import pytest

BASE_URL = os.environ.get("ASKPMO_BASE_URL", "http://localhost:8080")


@pytest.mark.integration
def test_health_through_nginx() -> None:
    """nginx proxies /api to a live api."""
    response = httpx.get(f"{BASE_URL}/api/health", timeout=10)
    assert response.status_code == 200


@pytest.mark.integration
def test_spa_served() -> None:
    """The SPA shell is served at /."""
    response = httpx.get(f"{BASE_URL}/", timeout=10)
    assert response.status_code == 200
    assert 'id="root"' in response.text
