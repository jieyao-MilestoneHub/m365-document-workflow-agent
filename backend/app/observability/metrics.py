"""Named metric primitives — counters and one histogram, exposed via a typed facade.

All metric names live here. Specialists never call OTel directly: they invoke the
facade functions (``record_specialist``, ``record_decision``, ...), which delegate to
lazily-created OpenTelemetry instruments — or to no-op stubs when ``opentelemetry`` is
not installed or instrumentation is disabled.

Why a module of free functions instead of a class: the OTel ``MeterProvider`` is already a
process-wide singleton; wrapping it in another class adds typing noise without isolation.
The facade keeps the *names* in one place (Single Responsibility) and the *vocabulary*
narrow (Interface Segregation — only two verbs leak out: counter ``add`` and histogram
``record``, hidden behind four typed helpers).
"""
from __future__ import annotations

from typing import Any

_METER_NAME = "ap-three-way-match"


class _NoopCounter:
    def add(
        self, value: float, attributes: dict[str, Any] | None = None
    ) -> None:  # pragma: no cover - trivial
        return None


class _NoopHistogram:
    def record(
        self, value: float, attributes: dict[str, Any] | None = None
    ) -> None:  # pragma: no cover - trivial
        return None


_instruments: dict[str, Any] = {}


def reset_instruments() -> None:
    """Clear the cache so the next facade call rebinds to the current MeterProvider.

    Required between tests when a test swaps in its own ``MeterProvider`` (or after
    ``configure_observability`` is called after the first metric emission).
    """
    _instruments.clear()


def _new_counter(name: str, description: str) -> Any:
    try:
        from opentelemetry import metrics as otel_metrics
    except ImportError:
        return _NoopCounter()
    try:
        return otel_metrics.get_meter(_METER_NAME).create_counter(name, description=description)
    except Exception:  # pragma: no cover - defensive
        return _NoopCounter()


def _new_histogram(name: str, description: str, unit: str) -> Any:
    try:
        from opentelemetry import metrics as otel_metrics
    except ImportError:
        return _NoopHistogram()
    try:
        return otel_metrics.get_meter(_METER_NAME).create_histogram(
            name, description=description, unit=unit
        )
    except Exception:  # pragma: no cover - defensive
        return _NoopHistogram()


def _counter(name: str, description: str) -> Any:
    inst = _instruments.get(name)
    if inst is None:
        inst = _new_counter(name, description)
        _instruments[name] = inst
    return inst


def _histogram(name: str, description: str, unit: str = "s") -> Any:
    inst = _instruments.get(name)
    if inst is None:
        inst = _new_histogram(name, description, unit)
        _instruments[name] = inst
    return inst


# --- public facade (this is the only surface specialists and supervisor call) -------------

TOOL_CALLS = "ap_three_way_match_tool_calls_total"
ROLE_VISIT = "ap_three_way_match_role_visit_total"
GUARDRAIL_VETO = "ap_three_way_match_guardrail_veto_total"
DECISION = "ap_three_way_match_decision_total"
SPECIALIST_LATENCY = "ap_three_way_match_specialist_latency_seconds"


def record_specialist(*, role: str, ok: bool, duration_s: float) -> None:
    """Record one specialist invocation: total count + latency histogram."""
    labels = {"role": role, "ok": "true" if ok else "false"}
    _counter(TOOL_CALLS, "Specialist invocations dispatched by the supervisor.").add(1, labels)
    _histogram(
        SPECIALIST_LATENCY, "Wall-clock latency of each specialist invocation.", unit="s"
    ).record(duration_s, labels)


def record_role_visit(*, role: str, attempt: int) -> None:
    _counter(ROLE_VISIT, "Times each specialist role is visited within a single run.").add(
        1, {"role": role, "attempt": str(attempt)}
    )


def record_veto(*, code: str) -> None:
    _counter(GUARDRAIL_VETO, "Preflight guardrail vetoes by code.").add(1, {"code": code})


def record_decision(*, decision: str) -> None:
    _counter(DECISION, "Terminal decisions emitted by the supervisor.").add(
        1, {"decision": decision}
    )
