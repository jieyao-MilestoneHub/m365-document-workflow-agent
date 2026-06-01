"""Shared builders for deterministic-core tests.

These construct schema objects directly (no cloud, no LLM) so the authoritative logic can be
tested in isolation.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.runner import DEFAULT_DATA_DIR
from app.schemas.enums import Decision, PostingDirection
from app.schemas.invoice import InvoiceLineItem, VendorInvoice
from app.schemas.policy import PolicyBundle, VendorConfig
from app.schemas.posting import PostingDraft, PostingLine


@pytest.fixture(scope="session")
def otel_in_memory_providers():
    """Install in-memory OTel tracer + meter providers exactly once per test session.

    OpenTelemetry's global ``set_tracer_provider`` / ``set_meter_provider`` are one-shot,
    so all tests that want to inspect spans or metrics must share a single provider pair.
    Tests use the per-test ``otel_recording`` fixture below to clear buffers between runs.

    Yields ``None`` when opentelemetry is not installed — consumer tests should
    ``pytest.importorskip("opentelemetry")`` at module level.
    """
    try:
        from opentelemetry import metrics as otel_metrics
        from opentelemetry import trace as otel_trace
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import InMemoryMetricReader
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
            InMemorySpanExporter,
        )
    except ImportError:
        yield None
        return

    from app.observability import metrics as obs_metrics

    span_exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    otel_trace.set_tracer_provider(tracer_provider)

    metric_reader = InMemoryMetricReader()
    meter_provider = MeterProvider(metric_readers=[metric_reader])
    otel_metrics.set_meter_provider(meter_provider)

    obs_metrics.reset_instruments()
    yield span_exporter, metric_reader


@pytest.fixture
def otel_recording(otel_in_memory_providers):
    """Per-test: clear span exporter and drain pending metrics from prior tests."""
    if otel_in_memory_providers is None:
        pytest.skip("opentelemetry not installed")
    span_exporter, metric_reader = otel_in_memory_providers
    span_exporter.clear()
    metric_reader.get_metrics_data()
    yield span_exporter, metric_reader


@pytest.fixture(scope="session")
def sample_data_dir() -> Path:
    """The synthetic-data directory, resolved by the runner (folder-move resilient).

    Tests requiring on-disk fixtures depend on this single source of truth rather than
    reconstructing paths, so reorganizing folders only requires changing the resolver.
    """
    assert DEFAULT_DATA_DIR.is_dir(), f"sample-data not found at {DEFAULT_DATA_DIR}"
    return DEFAULT_DATA_DIR


def _line(line_no: int, qty: str, unit: str) -> InvoiceLineItem:
    return InvoiceLineItem(
        line_no=line_no,
        description=f"Widget {line_no}",
        quantity=Decimal(qty),
        unit_price=Decimal(unit),
        line_total=Decimal(qty) * Decimal(unit),
    )


@pytest.fixture
def clean_invoice() -> VendorInvoice:
    """INV-1043: two lines, no tax, totals reconcile."""
    lines = [_line(1, "10", "9.75"), _line(2, "5", "20.00")]
    subtotal = sum((li.line_total for li in lines), Decimal("0"))
    return VendorInvoice(
        vendor_name="Globex",
        invoice_number="INV-1043",
        invoice_date=date(2026, 5, 20),
        currency="USD",
        subtotal=subtotal,
        tax_total=Decimal("0"),
        total=subtotal,
        po_ref="PO-5000",
        grn_ref="GRN-7000",
        line_items=lines,
    )


@pytest.fixture
def policy() -> PolicyBundle:
    return PolicyBundle(
        vendors=VendorConfig(hold_on_vendors=["Contoso"], gray_zone_vendors=["Acme-Lite"]),
    )


def balanced_posting(invoice_number: str = "INV-1043") -> PostingDraft:
    return PostingDraft(
        invoice_number=invoice_number,
        currency="USD",
        lines=[
            PostingLine(gl_account="2100", direction=PostingDirection.CREDIT, amount=Decimal("100.00")),
            PostingLine(gl_account="5000", direction=PostingDirection.DEBIT, amount=Decimal("100.00")),
        ],
        balanced=True,
    )


def unbalanced_posting(invoice_number: str = "INV-1042") -> PostingDraft:
    return PostingDraft(
        invoice_number=invoice_number,
        currency="USD",
        lines=[
            PostingLine(gl_account="2100", direction=PostingDirection.CREDIT, amount=Decimal("100.00")),
            PostingLine(gl_account="5000", direction=PostingDirection.DEBIT, amount=Decimal("90.00")),
        ],
    )


# re-exported for convenience in tests
PASS = Decision.PASS
HOLD = Decision.HOLD
ESCALATE = Decision.ESCALATE
