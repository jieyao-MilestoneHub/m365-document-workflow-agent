"""Narrow telemetry Protocols — three independently substitutable ports.

Split per ISP: a specialist that only emits metrics depends on :class:`MetricsPort` and
nothing else; the supervisor (which traces, logs, and meters) accepts all three. There is
deliberately no ``ObservabilityPort`` superset — bundling the three would force callers to
import abstractions they never use.

Concrete adapters are wired in :mod:`app.observability.config`; tests can supply any object
that conforms structurally (Protocols are ``runtime_checkable``).
"""
from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LoggerPort(Protocol):
    """Structured logger — keyword fields carry context (request_id, role, ...)."""

    def info(self, msg: str, /, **fields: Any) -> None: ...

    def warning(self, msg: str, /, **fields: Any) -> None: ...

    def error(self, msg: str, /, **fields: Any) -> None: ...

    def exception(self, msg: str, /, **fields: Any) -> None: ...


@runtime_checkable
class TracerPort(Protocol):
    """Open and close OpenTelemetry-style spans.

    Implementations return a context manager; the yielded value is opaque (an OTel ``Span``
    in production, ``None`` in the no-op stub). Callers must not depend on its shape.
    """

    def start_span(
        self,
        name: str,
        /,
        *,
        attrs: dict[str, Any] | None = None,
    ) -> AbstractContextManager[Any]: ...


@runtime_checkable
class MetricsPort(Protocol):
    """Counter increment + histogram observation. Two verbs, no more (ISP)."""

    def incr(
        self,
        name: str,
        /,
        *,
        value: int = 1,
        labels: dict[str, str] | None = None,
    ) -> None: ...

    def observe(
        self,
        name: str,
        /,
        *,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None: ...
