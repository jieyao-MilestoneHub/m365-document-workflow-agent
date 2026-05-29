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
