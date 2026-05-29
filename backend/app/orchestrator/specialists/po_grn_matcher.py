"""po_grn_matcher — match invoice lines against PO and GRN under the tolerance policy.

Depends only on a :class:`KnowledgePort` (Foundry IQ in prod). The fuzzy question (which PO
line corresponds to an invoice line) is resolved here deterministically by sku → description
→ position; the *numbers* (deltas, tolerance) come from :mod:`app.orchestrator.matching`.
"""
from __future__ import annotations

from decimal import Decimal

from app.schemas.enums import LineStatus
from app.schemas.invoice import VendorInvoice
from app.schemas.match import LineMatch, ThreeWayMatchReport
from app.schemas.reference import GoodsReceiptNote, PurchaseOrder

from ..envelope import MultiAgentEnvelope, SpecialistResult
from ..matching import evaluate_line_tolerance, roll_up_match_status
from ..ports import KnowledgePort
from ..roles import INVOICE_EXTRACTOR, PO_GRN_MATCHER


def _find_index(sku: str | None, description: str, candidates: list) -> int | None:
    """Resolve a reference line by sku, then case-insensitive description, then None."""
    if sku:
        for i, c in enumerate(candidates):
            if c.sku and c.sku == sku:
                return i
    desc = description.strip().lower()
    for i, c in enumerate(candidates):
        if c.description.strip().lower() == desc:
            return i
    return None


class PoGrnMatcher:
    role = PO_GRN_MATCHER

    def __init__(self, knowledge: KnowledgePort) -> None:
        self._knowledge = knowledge

    def run(self, envelope: MultiAgentEnvelope) -> SpecialistResult:
        invoice: VendorInvoice | None = envelope.payload_for(INVOICE_EXTRACTOR)
        if invoice is None:
            return SpecialistResult(role=self.role, error="no upstream invoice to match")

        tolerance = envelope.policy.tolerance
        po, po_cites = self._knowledge.get_purchase_order(po_ref=invoice.po_ref)
        grn, grn_cites = self._knowledge.get_goods_receipt(grn_ref=invoice.grn_ref)

        currency_mismatch = po is not None and invoice.currency != po.currency
        invoiced_to_date = self._knowledge.get_invoiced_to_date(po_ref=invoice.po_ref)
        lines = [
            self._match_line(li, po, grn, tolerance, currency_mismatch, invoiced_to_date)
            for li in invoice.line_items
        ]
        report = ThreeWayMatchReport(
            invoice_number=invoice.invoice_number,
            po_number=po.po_number if po else None,
            grn_number=grn.grn_number if grn else None,
            po_currency=po.currency if po else None,
            currency_mismatch=currency_mismatch,
            match_status=roll_up_match_status(
                has_line_items=bool(invoice.line_items),
                po_present=po is not None,
                grn_present=grn is not None,
                all_lines_matched=all(m.status is LineStatus.MATCHED for m in lines),
                all_within_tolerance=all(m.within_tolerance for m in lines),
            ),
            lines=lines,
            tolerance_version=tolerance.version,
            citations=list(po_cites) + list(grn_cites),
        )
        summary = f"Matched {len(lines)} lines against " \
                  f"PO {report.po_number or '—'} / GRN {report.grn_number or '—'}: " \
                  f"{report.match_status.value}."
        return SpecialistResult(
            role=self.role, payload=report, citations=tuple(report.citations), summary=summary
        )

    def _match_line(self, li, po: PurchaseOrder | None, grn: GoodsReceiptNote | None,
                    tolerance, currency_mismatch: bool = False,
                    invoiced_to_date: dict[str, Decimal] | None = None):
        po_idx = _find_index(li.sku, li.description, po.lines) if po else None
        grn_idx = _find_index(li.sku, li.description, grn.lines) if grn else None

        if po_idx is None:
            return LineMatch(invoice_line_no=li.line_no, status=LineStatus.MISSING_IN_PO,
                             note="no matching PO line")
        if grn_idx is None:
            return LineMatch(invoice_line_no=li.line_no, po_line_idx=po_idx,
                             status=LineStatus.MISSING_IN_GRN, note="no matching GRN line")

        po_line, grn_line = po.lines[po_idx], grn.lines[grn_idx]
        qty_delta = li.quantity - grn_line.received_quantity
        # Cross-currency price deltas are meaningless; the report-level currency_mismatch
        # flag escalates instead, so suppress the per-line price comparison here.
        price_delta = Decimal("0") if currency_mismatch else li.unit_price - po_line.unit_price
        within = evaluate_line_tolerance(
            quantity_delta=qty_delta, price_delta=price_delta,
            po_unit_price=po_line.unit_price, tolerance=tolerance,
        )

        # line-level billing position: bill no more than what's received-but-unbilled
        billed_before = (invoiced_to_date or {}).get(li.sku or li.description, Decimal("0"))
        remaining_billable = grn_line.received_quantity - billed_before
        over_billed = li.quantity > remaining_billable

        return LineMatch(
            invoice_line_no=li.line_no, po_line_idx=po_idx, grn_line_idx=grn_idx,
            po_unit_price=po_line.unit_price,
            status=self._status(within, qty_delta, price_delta),
            quantity_delta=qty_delta, price_delta=price_delta, within_tolerance=within,
            received_quantity=grn_line.received_quantity,
            invoiced_to_date_quantity=billed_before,
            remaining_billable_quantity=remaining_billable,
            over_billed=over_billed,
        )

    @staticmethod
    def _status(within: bool, qty_delta: Decimal, price_delta: Decimal) -> LineStatus:
        if within:
            return LineStatus.MATCHED
        if price_delta.copy_abs() > 0:
            return LineStatus.PRICE_VARIANCE
        if qty_delta.copy_abs() > 0:
            return LineStatus.QUANTITY_VARIANCE
        return LineStatus.UNMATCHED
