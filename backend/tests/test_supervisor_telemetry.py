"""PR3 — supervisor span hierarchy + per-role metrics.

Uses the session-wide in-memory OpenTelemetry providers installed by
``conftest.otel_in_memory_providers`` so the Application Insights wire contract can be
asserted without an Azure subscription. The Azure Monitor exporter consumes the same
OTel ``Span`` / ``Counter`` / ``Histogram`` shapes — passing here means the production
exporter will see the same data.
"""
from __future__ import annotations

import pytest

pytest.importorskip("opentelemetry")

from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from app.observability import metrics
from app.runner import run


def _metric_names(reader: InMemoryMetricReader) -> set[str]:
    data = reader.get_metrics_data()
    if data is None:
        return set()
    return {
        m.name
        for rm in data.resource_metrics
        for sm in rm.scope_metrics
        for m in sm.metrics
    }


def _decisions_emitted(reader: InMemoryMetricReader) -> list[str]:
    data = reader.get_metrics_data()
    if data is None:
        return []
    decisions: list[str] = []
    for rm in data.resource_metrics:
        for sm in rm.scope_metrics:
            for m in sm.metrics:
                if m.name != metrics.DECISION:
                    continue
                for dp in m.data.data_points:
                    val = dp.attributes.get("decision")
                    if val is not None:
                        decisions.append(str(val))
    return decisions


def test_supervisor_opens_parent_span_with_invoice_ref(otel_recording):
    span_exporter, _ = otel_recording
    run("INV-1043")

    parents = [s for s in span_exporter.get_finished_spans() if s.name == "invoke_supervisor"]
    assert len(parents) == 1
    assert parents[0].attributes.get("invoice.ref") == "INV-1043"


def test_specialist_invocations_are_child_spans(otel_recording):
    span_exporter, _ = otel_recording
    run("INV-1043")

    spans = span_exporter.get_finished_spans()
    parent = next(s for s in spans if s.name == "invoke_supervisor")
    children = [s for s in spans if s.name == "specialist.invoke"]

    # Five specialists in the clean-path pipeline, each invoked exactly once.
    assert len(children) == 5
    roles = {s.attributes["specialist.role"] for s in children}
    assert roles == {
        "invoice_extractor",
        "po_grn_matcher",
        "variance_assessor",
        "posting_preparer",
        "exception_reviewer",
    }
    parent_id = parent.context.span_id
    assert all(s.parent and s.parent.span_id == parent_id for s in children)


def test_traceevent_carries_trace_and_span_ids_when_otel_active(otel_recording):
    _ = otel_recording
    result = run("INV-1043")
    for event in result.events:
        assert event.trace_id and len(event.trace_id) == 32
        assert event.span_id and len(event.span_id) == 16


def test_decision_and_latency_metrics_recorded_for_clean_run(otel_recording):
    _, reader = otel_recording
    run("INV-1043")
    names = _metric_names(reader)
    assert metrics.DECISION in names
    assert metrics.SPECIALIST_LATENCY in names
    assert metrics.TOOL_CALLS in names
    assert metrics.ROLE_VISIT in names


def test_variance_path_records_hold_decision(otel_recording):
    _, reader = otel_recording
    run("INV-1042")
    assert "hold" in _decisions_emitted(reader)
