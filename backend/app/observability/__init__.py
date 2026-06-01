"""Log, trace, metrics, and error-handling primitives shared by the API and the orchestrator.

Each submodule degrades to a no-op when its optional dependency
(``opentelemetry``, ``redactkit``, or ``agent_framework``) is absent, so the deterministic
core stays importable and runnable without any cloud credentials.
"""
from __future__ import annotations

from . import metrics, tracing
from .config import configure_observability, is_enabled
from .correlation import (
    REQUEST_ID_HEADER,
    TRACEPARENT_HEADER,
    CorrelationMiddleware,
    request_id,
    traceparent,
)
from .exceptions import (
    AppError,
    NotFoundError,
    UpstreamError,
    ValidationError,
    register_exception_handlers,
)
from .ports import LoggerPort, MetricsPort, TracerPort

__all__ = [
    "AppError",
    "CorrelationMiddleware",
    "LoggerPort",
    "MetricsPort",
    "NotFoundError",
    "REQUEST_ID_HEADER",
    "TRACEPARENT_HEADER",
    "TracerPort",
    "UpstreamError",
    "ValidationError",
    "configure_observability",
    "is_enabled",
    "metrics",
    "register_exception_handlers",
    "request_id",
    "traceparent",
    "tracing",
]
