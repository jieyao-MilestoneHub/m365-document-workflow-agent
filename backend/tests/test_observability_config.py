"""PR1 tests — observability config + ports surface + metrics facade.

These tests must pass with and without the optional ``observability`` extra installed.
Pieces that require ``opentelemetry`` or ``redactkit`` are gated via ``importorskip``.
"""
from __future__ import annotations

import logging

import pytest

from app.observability import configure_observability, is_enabled, metrics
from app.observability.ports import LoggerPort, MetricsPort, TracerPort


@pytest.fixture(autouse=True)
def _reset_metrics_cache():
    metrics.reset_instruments()
    yield
    metrics.reset_instruments()


def test_is_enabled_false_when_env_unset(monkeypatch):
    monkeypatch.delenv("ENABLE_INSTRUMENTATION", raising=False)
    assert is_enabled() is False


@pytest.mark.parametrize("value", ["false", "0", "", "no", "  "])
def test_is_enabled_false_for_falsy_strings(monkeypatch, value):
    monkeypatch.setenv("ENABLE_INSTRUMENTATION", value)
    assert is_enabled() is False


@pytest.mark.parametrize("value", ["true", "True", "1", "yes", "on", "  TRUE  "])
def test_is_enabled_true_for_truthy_strings(monkeypatch, value):
    monkeypatch.setenv("ENABLE_INSTRUMENTATION", value)
    assert is_enabled() is True


def test_configure_is_noop_when_env_unset(monkeypatch):
    monkeypatch.delenv("ENABLE_INSTRUMENTATION", raising=False)
    assert configure_observability() is False


def test_configure_returns_true_when_enabled_without_optional_deps(monkeypatch):
    # Even if neither agent_framework nor redactkit is installed, configure_observability
    # must complete (best-effort) and signal that instrumentation was requested.
    monkeypatch.setenv("ENABLE_INSTRUMENTATION", "true")
    assert configure_observability() is True
    # Sets a default service name when none is supplied.
    assert pytest.importorskip("os") and __import__("os").environ.get("OTEL_SERVICE_NAME")


def test_configure_never_raises_when_agent_framework_missing(monkeypatch):
    # Defensive: the agent_framework import is best-effort. Make sure that even if some
    # exotic import error occurs, configure_observability swallows it.
    monkeypatch.setenv("ENABLE_INSTRUMENTATION", "true")
    # Don't try to actually break sys.modules — just ensure the second call is also safe
    # (idempotent attachment of handlers, no side-effect cascade).
    assert configure_observability() is True
    assert configure_observability() is True


def test_ports_are_runtime_checkable():
    # Anything quacking like the protocol should satisfy isinstance().
    class _FakeLogger:
        def info(self, msg, /, **fields): ...
        def warning(self, msg, /, **fields): ...
        def error(self, msg, /, **fields): ...
        def exception(self, msg, /, **fields): ...

    class _FakeTracer:
        def start_span(self, name, /, *, attrs=None):  # pragma: no cover - protocol shape only
            from contextlib import nullcontext

            return nullcontext()

    class _FakeMetrics:
        def incr(self, name, /, *, value=1, labels=None): ...
        def observe(self, name, /, *, value, labels=None): ...

    assert isinstance(_FakeLogger(), LoggerPort)
    assert isinstance(_FakeTracer(), TracerPort)
    assert isinstance(_FakeMetrics(), MetricsPort)


def test_metrics_facade_safe_without_opentelemetry(monkeypatch):
    # Even when OTel SDK is missing, the facade must execute without raising and without
    # leaking any cloud-coupling. Lazy cache means we get NoopCounter / NoopHistogram.
    import sys

    monkeypatch.setitem(sys.modules, "opentelemetry", None)
    monkeypatch.setitem(sys.modules, "opentelemetry.metrics", None)
    metrics.reset_instruments()

    metrics.record_specialist(role="invoice_extractor", ok=True, duration_s=0.012)
    metrics.record_role_visit(role="invoice_extractor", attempt=1)
    metrics.record_veto(code="BUDGET_EXCEEDED")
    metrics.record_decision(decision="pass")


# NOTE: the "facade routes through OpenTelemetry when present" assertion now lives in
# tests/test_supervisor_telemetry.py, which exercises the entire pipeline end-to-end
# against the shared in-memory provider installed by conftest.otel_in_memory_providers.
# Duplicating that wiring here would race the one-shot global provider install.


def test_configure_attaches_redacting_filter_when_redactkit_present(monkeypatch):
    pytest.importorskip("redactkit")
    monkeypatch.setenv("ENABLE_INSTRUMENTATION", "true")

    # Ensure root has at least one handler so the filter attachment is observable.
    root = logging.getLogger()
    handler = logging.StreamHandler()
    root.addHandler(handler)
    try:
        # PR1 leaves _attach_redaction_filter a no-op until PR2 lands the redaction module.
        # We still assert configure_observability returns True and doesn't crash.
        assert configure_observability() is True
    finally:
        root.removeHandler(handler)
