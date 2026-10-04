"""FastAPI application factory and process entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.routers import health, profiles
from pmo_core import telemetry
from pmo_core.container import Container, bootstrap, build_container
from pmo_core.settings import get_settings

_logger = structlog.get_logger(__name__)


def create_app(
    container_factory: Callable[[], Container] | None = None,
    run_bootstrap: bool = True,
) -> FastAPI:
    """Create the app; tests pass a factory that returns a container of fakes."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Build adapters once; run migrations and create index, container and queue."""
        settings = get_settings()
        app.state.tracer = telemetry.setup("api", settings)
        container = container_factory() if container_factory else build_container(settings)
        if run_bootstrap:
            bootstrap(container)
            _logger.info("bootstrap_complete")
        app.state.container = container
        yield

    app = FastAPI(title="askPMO API", version="0.1.0", lifespan=lifespan)
    app.include_router(health.router, prefix="/api")
    app.include_router(profiles.router, prefix="/api")

    @app.exception_handler(StarletteHTTPException)
    async def http_problem(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Render HTTP errors as RFC 7807 problem details."""
        return _problem(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_problem(_: Request, exc: RequestValidationError) -> JSONResponse:
        """Render validation errors as RFC 7807 problem details."""
        return _problem(422, "Request validation failed", errors=exc.errors())

    return app


def _problem(status: int, detail: str, **extra: object) -> JSONResponse:
    """Build an `application/problem+json` response."""
    body: dict[str, object] = {
        "type": "about:blank",
        "title": _title(status),
        "status": status,
        "detail": detail,
    }
    body.update(extra)
    return JSONResponse(body, status_code=status, media_type="application/problem+json")


def _title(status: int) -> str:
    """Return the standard reason phrase for a status code."""
    from http import HTTPStatus

    try:
        return HTTPStatus(status).phrase
    except ValueError:
        return "Error"


def run() -> None:
    """Start uvicorn (container entry point)."""
    import uvicorn

    uvicorn.run(create_app(), host="0.0.0.0", port=8000, log_config=None)


if __name__ == "__main__":
    run()
