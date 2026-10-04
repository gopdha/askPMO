"""FastAPI dependencies."""

from __future__ import annotations

from fastapi import Request

from pmo_core.container import Container


def get_container(request: Request) -> Container:
    """Return the process container built at startup."""
    container: Container = request.app.state.container
    return container
