"""Vendor invoice schema — the output of the invoice_extractor specialist.

Arithmetic invariants are enforced at construction (Pydantic), so a downstream specialist
can trust the numbers. The extractor must omit unreadable lines rather than fabricate them.
"""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import LineCharge
from .money import money_close

_INVOICE_NUMBER_RE = re.compile(r"^[A-Za-z0-9_\-./]{1,128}$")


class InvoiceLineItem(BaseModel):
    """A single invoice line. ``line_total`` must equal quantity × unit_price."""

    model_config = ConfigDict(frozen=True)

    line_no: int = Field(ge=1)
    sku: str | None = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    tax_rate: Decimal | None = None
    #: what this line is. Only ``good`` lines are three-way matched; charge lines
    #: (freight/misc/discount) are routed and governed separately. Defaults to ``good``
    #: so existing fixtures/payloads are unaffected.
    charge_type: LineCharge = LineCharge.GOOD
    #: unit the line is billed in (e.g. "ea", "case"). When it differs from the PO unit,
    #: a ``uom_factor`` must convert it to the PO unit or the line cannot be reconciled.
    unit_of_measure: str | None = None
    #: multiplier converting this line's UOM to the PO/GRN base UOM (qty × factor = base qty)
    uom_factor: Decimal = Decimal("1")

    @model_validator(mode="after")
    def _check_line_arithmetic(self) -> "InvoiceLineItem":
        expected = self.quantity * self.unit_price
        if not money_close(self.line_total, expected):
            raise ValueError(
                f"line {self.line_no}: line_total {self.line_total} != "
                f"quantity×unit_price ({expected})"
            )
        return self


class InvoiceAllowance(BaseModel):
    """A promotion/trade allowance the supplier credited on this invoice.

    Tracked separately from the line items (NOT folded into ``subtotal``/``total``) so the
    arithmetic invariants stay clean and the *absence* of an allowance is provable: an invoice
    that should carry an allowance but lists none has ``allowances == []``. The retail control
    reconciles ``Σ amount`` here against the expected allowance from the promotion agreement.
    """

    model_config = ConfigDict(frozen=True)

    promo_id: str | None = None
    sku: str | None = None
    amount: Decimal = Field(ge=0, description="allowance credited (currency units)")
    description: str | None = None


class VendorInvoice(BaseModel):
    """Structured vendor invoice. Totals must reconcile to the line items."""

    model_config = ConfigDict(frozen=True)

    vendor_name: str
    vendor_id: str | None = None
    invoice_number: str
    invoice_date: date
    due_date: date | None = None
    currency: str = Field(min_length=3, max_length=3, description="ISO 4217")
    subtotal: Decimal
    tax_total: Decimal = Field(ge=0)
    total: Decimal
    po_ref: str | None = None
    grn_ref: str | None = None
    line_items: list[InvoiceLineItem] = Field(default_factory=list, max_length=2000)
    #: promotion/trade allowances the supplier credited on this invoice (default: none applied)
    allowances: list[InvoiceAllowance] = Field(default_factory=list)
    #: fields the extractor could not read with confidence (drives quality warnings)
    missing_fields: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_invoice_arithmetic(self) -> "VendorInvoice":
        if not _INVOICE_NUMBER_RE.match(self.invoice_number):
            raise ValueError(f"invalid invoice_number: {self.invoice_number!r}")
        if self.line_items:
            lines_sum = sum((li.line_total for li in self.line_items), Decimal("0"))
            if not money_close(self.subtotal, lines_sum):
                raise ValueError(f"subtotal {self.subtotal} != sum(line_total) ({lines_sum})")
        if not money_close(self.total, self.subtotal + self.tax_total):
            raise ValueError(
                f"total {self.total} != subtotal+tax_total ({self.subtotal + self.tax_total})"
            )
        return self
