"""Retail deduction-control schemas.

Two payloads:

* :class:`AllowanceAudit` — output of the ``promotion_auditor`` specialist: the per-promotion
  reconciliation of expected vs applied allowance, and the resulting margin leakage.
* :class:`DeductionCase` — assembled by the deterministic decision matrix for each disputable
  finding (promotion leakage, short receipt / over-billing). It is the auditable, supplier-facing
  packet: a disputed amount, evidence references, a generated explanation, and a routing target.

Money is always :class:`decimal.Decimal`.
"""
from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from .citation import Citation
from .promotion import Promotion


class DeductionType(str, Enum):
    """Closed set of retail deduction-case types."""

    PROMOTION_ALLOWANCE_MISSING = "PROMOTION_ALLOWANCE_MISSING"
    SHORT_RECEIPT = "SHORT_RECEIPT"


class AllowanceLine(BaseModel):
    """Per-promotion reconciliation for one SKU on the invoice."""

    model_config = ConfigDict(frozen=True)

    promo_id: str
    sku: str | None = None
    billed_quantity: Decimal = Decimal("0")
    expected_allowance: Decimal = Field(default=Decimal("0"), description="owed per the agreement")
    applied_allowance: Decimal = Field(default=Decimal("0"), description="credited on the invoice")
    leakage: Decimal = Field(default=Decimal("0"), description="max(0, expected − applied)")
    affected_lines: list[int] = Field(default_factory=list)


class AllowanceAudit(BaseModel):
    """promotion_auditor output: allowance reconciliation for one invoice."""

    model_config = ConfigDict(frozen=True)

    invoice_number: str
    lines: list[AllowanceLine] = Field(default_factory=list)
    margin_leakage_total: Decimal = Field(default=Decimal("0"))
    applicable_promotions: list[Promotion] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)


class DeductionCase(BaseModel):
    """An auditable, disputable, supplier-facing deduction packet."""

    model_config = ConfigDict(frozen=True)

    deduction_case_id: str
    invoice_number: str
    vendor_name: str
    deduction_type: DeductionType
    amount: Decimal = Field(ge=0, description="disputed / held amount (currency units)")
    status: str = "OPEN"
    supplier_dispute_allowed: bool = True
    affected_lines: list[int] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    supplier_explanation: str = ""
    route_to: str = "ap_manager"
