"""Liveness and readiness."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from api.deps import get_container
from api.schemas import HealthOut, ReadyCheck, ReadyOut
from pmo_core.container import Container

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    """Liveness: the process is up."""
    return HealthOut(status="ok")


@router.get("/ready", response_model=ReadyOut, responses={503: {"model": ReadyOut}})
def ready(container: Annotated[Container, Depends(get_container)]) -> JSONResponse:
    """Readiness: index, database, queue and Foundry reachable; 503 otherwise."""
    checks = {name: ReadyCheck(**result) for name, result in container.readiness().items()}
    body = ReadyOut(ready=all(check.ok for check in checks.values()), checks=checks)
    return JSONResponse(body.model_dump(), status_code=200 if body.ready else 503)
