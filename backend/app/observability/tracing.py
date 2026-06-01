"""Tracing facade — one function (:func:`start_span`) usable with or without OpenTelemetry.

Mirrors the design of :mod:`app.observability.metrics`: the supervisor and any future
specialist that wants to emit a span imports the *function*, not the OTel API directly.
When ``opentelemetry`` is not installed, every call yields ``None`` and the supervisor's
control flow is unaffected.

When OTel is installed but the global tracer provider is the no-op default (i.e.
``ENABLE_INSTRUMENTATION`` is unset), ``tracer.start_as_current_span`` still works — it
just produces a no-op span, no exporter is called, and there is zero network cost.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

_TRACER_NAME = "ap-three-way-match"


@contextmanager
def start_span(name: str, *, attrs: dict[str, Any] | None = None) -> Iterator[Any]:
    """Open an OTel span (or yield ``None`` when opentelemetry is unavailable)."""
    try:
        from opentelemetry import trace as otel_trace
    except ImportError:
        yield None
        return

    tracer = otel_trace.get_tracer(_TRACER_NAME)
    with tracer.start_as_current_span(name, attributes=attrs or {}) as span:
        yield span


def current_trace_and_span_id() -> tuple[str | None, str | None]:
    """``(trace_id, span_id)`` of the current span, or ``(None, None)`` when inactive."""
    try:
        from opentelemetry import trace as otel_trace
    except ImportError:
        return None, None

    span = otel_trace.get_current_span()
    ctx = span.get_span_context()
    if not ctx.is_valid:
        return None, None
    return format(ctx.trace_id, "032x"), format(ctx.span_id, "016x")


def set_status_error(span: Any, message: str) -> None:
    """Mark ``span`` as ERROR. No-op when ``span`` is ``None`` or OTel is absent."""
    if span is None:
        return
    try:
        from opentelemetry.trace import Status, StatusCode
    except ImportError:
        return
    try:
        span.set_status(Status(StatusCode.ERROR, message))
    except Exception:  # pragma: no cover - defensive
        pass
