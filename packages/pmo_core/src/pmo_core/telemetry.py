"""Tracing and structured logging setup shared by api, worker and eval.

Arize AX export is wired in P2; until then (and whenever `ARIZE_API_KEY` is empty) a no-op tracer is used.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterator, MutableMapping
from contextlib import contextmanager
from typing import Any

import structlog
from opentelemetry import trace

from pmo_core.settings import Settings

SPAN_CHAT = "chat"
_logger = structlog.get_logger(__name__)


def configure_logging(service_name: str, level: str = "INFO") -> None:
    """Emit JSON log lines with service and level; never log prompts or answers."""
    logging.basicConfig(stream=sys.stdout, level=level.upper(), format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _add_trace_ids,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level.upper())),
        logger_factory=structlog.PrintLoggerFactory(),
    )
    structlog.contextvars.bind_contextvars(service=service_name)


def _add_trace_ids(_: Any, __: str, event_dict: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Attach the current trace and span IDs to every log line."""
    span_context = trace.get_current_span().get_span_context()
    if span_context.is_valid:
        event_dict["trace_id"] = format(span_context.trace_id, "032x")
        event_dict["span_id"] = format(span_context.span_id, "016x")
    return event_dict


def setup(service_name: str, settings: Settings) -> trace.Tracer:
    """Configure logging and return a tracer (no-op when Arize is not configured)."""
    configure_logging(service_name, settings.log_level)
    if not settings.arize_api_key:
        _logger.warning("arize_not_configured", detail="tracing disabled; using no-op tracer")
        return trace.NoOpTracer()
    # Arize registration is added in P2.
    return trace.get_tracer(service_name)


@contextmanager
def stage_span(tracer: trace.Tracer, name: str, **attributes: Any) -> Iterator[trace.Span]:
    """Run a pipeline stage inside a named span."""
    with tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        yield span
