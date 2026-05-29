from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.enums import BlockingReason, Decision
from app.schemas.invoice import InvoiceLineItem, VendorInvoice
from app.schemas.outcome import ValidationOutcome


def test_line_item_rejects_bad_arithmetic():
    with pytest.raises(ValidationError):
        InvoiceLineItem(
            line_no=1, description="x", quantity=Decimal("2"),
            unit_price=Decimal("5.00"), line_total=Decimal("9.00"),
        )


def test_invoice_rejects_total_mismatch():
    with pytest.raises(ValidationError):
        VendorInvoice(
            vendor_name="V", invoice_number="INV-1", invoice_date=date(2026, 1, 1),
            currency="USD", subtotal=Decimal("10.00"), tax_total=Decimal("1.00"),
            total=Decimal("99.00"),
        )


def test_invoice_rejects_subtotal_not_matching_lines(clean_invoice):
    bad_lines = clean_invoice.line_items
    with pytest.raises(ValidationError):
        VendorInvoice(
            vendor_name="V", invoice_number="INV-2", invoice_date=date(2026, 1, 1),
            currency="USD", subtotal=Decimal("1.00"), tax_total=Decimal("0"),
            total=Decimal("1.00"), line_items=bad_lines,
        )


def test_outcome_pass_requires_empty_blocking_reasons():
    with pytest.raises(ValidationError):
        ValidationOutcome(
            invoice_number="INV-1", decision=Decision.PASS, confidence=0.9,
            blocking_reasons=[BlockingReason.VENDOR_GRAY_ZONE], summary="x",
        )


def test_outcome_non_pass_requires_a_blocking_reason():
    with pytest.raises(ValidationError):
        ValidationOutcome(
            invoice_number="INV-1", decision=Decision.HOLD, confidence=0.8,
            blocking_reasons=[], summary="x",
        )
