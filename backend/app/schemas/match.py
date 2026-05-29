"""Three-way match report — output of the po_grn_matcher specialist."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from .citation import Citation
from .enums import LineStatus, MatchStatus


class LineMatch(BaseModel):
    """Per-invoice-line match result against PO and GRN."""

    model_config = ConfigDict(frozen=True)

    invoice_line_no: int
    po_line_idx: int | None = None
    grn_line_idx: int | None = None
    status: LineStatus
    #: invoice.quantity - grn.received_quantity (signed; + = over-receipt)
    quantity_delta: Decimal = Decimal("0")
    #: invoice.unit_price - po.unit_price (signed; + = overbilled)
    price_delta: Decimal = Decimal("0")
    within_tolerance: bool = True
    note: str | None = None


class ThreeWayMatchReport(BaseModel):
    """Roll-up of the three-way match across all invoice lines."""

    model_config = ConfigDict(frozen=True)

    invoice_number: str
    po_number: str | None = None
    grn_number: str | None = None
    match_status: MatchStatus
    lines: list[LineMatch] = Field(default_factory=list)
    tolerance_version: str = "2026.04.1"
    citations: list[Citation] = Field(default_factory=list)
