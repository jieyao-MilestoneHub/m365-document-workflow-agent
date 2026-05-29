from datetime import date
from decimal import Decimal

from app.orchestrator.validators import (
    check_gl_accounts,
    check_posting_balance,
    check_posting_period,
    check_tax_consistency,
)
from app.schemas.enums import BlockingReason
from app.schemas.invoice import InvoiceLineItem, VendorInvoice
from app.schemas.policy import PolicyBundle

from .conftest import balanced_posting, unbalanced_posting


def _taxed_invoice(tax_total: str) -> VendorInvoice:
    line = InvoiceLineItem(
        line_no=1, description="x", quantity=Decimal("1"),
        unit_price=Decimal("100.00"), line_total=Decimal("100.00"), tax_rate=Decimal("0.10"),
    )
    return VendorInvoice(
        vendor_name="Globex", invoice_number="INV-T", invoice_date=date(2026, 5, 20),
        currency="USD", subtotal=Decimal("100.00"), tax_total=Decimal(tax_total),
        total=Decimal("100.00") + Decimal(tax_total), line_items=[line],
    )


def test_balanced_posting_passes():
    assert check_posting_balance(balanced_posting()).ok is True


def test_unbalanced_posting_flags_reason():
    verdict = check_posting_balance(unbalanced_posting())
    assert verdict.reason is BlockingReason.POSTING_DRAFT_UNBALANCED


def test_gl_check_skipped_without_allowlist():
    assert check_gl_accounts(balanced_posting(), PolicyBundle()).ok is True


def test_gl_check_flags_unknown_account():
    policy = PolicyBundle(valid_gl_accounts=frozenset({"2100"}))  # 5000 missing
    verdict = check_gl_accounts(balanced_posting(), policy)
    assert verdict.reason is BlockingReason.GL_ACCOUNT_INVALID


def test_closed_period_flagged(clean_invoice):
    policy = PolicyBundle(closed_periods=frozenset({"2026-05"}))
    verdict = check_posting_period(clean_invoice, policy)
    assert verdict.reason is BlockingReason.POSTING_PERIOD_CLOSED


def test_open_period_passes(clean_invoice):
    assert check_posting_period(clean_invoice, PolicyBundle()).ok is True


def test_tax_consistency_skipped_without_rates(clean_invoice):
    assert check_tax_consistency(clean_invoice).ok is True


def test_tax_consistency_passes_when_matching():
    assert check_tax_consistency(_taxed_invoice("10.00")).ok is True


def test_tax_discrepancy_flagged():
    verdict = check_tax_consistency(_taxed_invoice("5.00"))
    assert verdict.reason is BlockingReason.TAX_DISCREPANCY
