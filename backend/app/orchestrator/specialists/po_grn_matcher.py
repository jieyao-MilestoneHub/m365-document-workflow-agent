"""po_grn_matcher — match invoice lines against PO and GRN under the tolerance policy.

Depends only on a :class:`KnowledgePort` (Foundry IQ in prod). The fuzzy question (which PO
line corresponds to an invoice line) is resolved here deterministically by sku → description
→ position; the *numbers* (deltas, tolerance) come from :mod:`app.orchestrator.matching`.
"""
from __future__ import annotations

from decimal import Decimal

from app.schemas.enums import LineCharge, LineStatus
from app.schemas.invoice import VendorInvoice
from app.schemas.match import LineMatch, ThreeWayMatchReport
from app.schemas.reference import GoodsReceiptNote, PurchaseOrder

from ..envelope import MultiAgentEnvelope, SpecialistResult
from ..matching import evaluate_line_tolerance, roll_up_match_status
from ..ports import KnowledgePort
from ..roles import INVOICE_EXTRACTOR, PO_GRN_MATCHER


def _find_index(
    sku: str | None, description: str, candidates: list, aliases: dict[str, str]
) -> tuple[int | None, str | None]:
    """Resolve a reference line, returning (index, matched_by).

    matched_by is "sku" (direct), "alias" (vendor SKU mapped to internal), or "description".
    """
    internal = aliases.get(sku, sku) if sku else None
    if internal:
        for i, c in enumerate(candidates):
            if c.sku and c.sku == internal:
                return i, ("alias" if internal != sku else "sku")
    desc = description.strip().lower()
    for i, c in enumerate(candidates):
        if c.description.strip().lower() == desc:
            return i, "description"
    return None, None


def _uom_reconcilable(invoice_line, po_line) -> bool:
    """True unless the invoice and PO units differ with no conversion factor to bridge them.

    Reconcilable when either side omits a UOM, the units match, or an explicit
    ``uom_factor`` (≠ 1) is supplied to convert the invoice UOM into the PO UOM.
    """
    inv_uom = (invoice_line.unit_of_measure or "").strip().lower()
    po_uom = (po_line.unit_of_measure or "").strip().lower()
    if not inv_uom or not po_uom or inv_uom == po_uom:
        return True
    return invoice_line.uom_factor != Decimal("1")


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
        aliases = envelope.policy.sku_aliases
        lines = [
            self._match_line(li, po, grn, tolerance, currency_mismatch, invoiced_to_date, aliases)
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
                    invoiced_to_date: dict[str, Decimal] | None = None,
                    aliases: dict[str, str] | None = None):
        # Charge lines (freight/misc/discount) have no PO/GRN counterpart — skip the
        # three-way match entirely and emit a neutral result. They are governed by
        # freight_tolerance (decision.py) and routed in posting, not matched here.
        if li.charge_type is not LineCharge.GOOD:
            return LineMatch(
                invoice_line_no=li.line_no, status=LineStatus.MATCHED,
                within_tolerance=True, over_billed=False,
                note=f"{li.charge_type.value} charge — not subject to three-way match",
            )

        aliases = aliases or {}
        po_idx, po_method = _find_index(li.sku, li.description, po.lines, aliases) if po else (None, None)
        grn_idx, _ = _find_index(li.sku, li.description, grn.lines, aliases) if grn else (None, None)

        if po_idx is None:
            return LineMatch(invoice_line_no=li.line_no, status=LineStatus.MISSING_IN_PO,
                             note="no matching PO line")
        if grn_idx is None:
            return LineMatch(invoice_line_no=li.line_no, po_line_idx=po_idx,
                             status=LineStatus.MISSING_IN_GRN, note="no matching GRN line")

        po_line, grn_line = po.lines[po_idx], grn.lines[grn_idx]
        resolved_sku = aliases.get(li.sku, li.sku) if li.sku else None
        alias_unresolved = po_method == "description" and bool(li.sku) and li.sku not in aliases
        # Normalize the invoice quantity into the PO/GRN base UOM before comparing. A UOM that
        # differs from the PO with no conversion factor cannot be reconciled — a silent unit
        # error is high-$, so flag it and force a non-matched status (decision.py escalates).
        uom_mismatch = not _uom_reconcilable(li, po_line)
        qty_delta = (li.quantity * li.uom_factor) - grn_line.received_quantity
        # Cross-currency price deltas are meaningless; the report-level currency_mismatch
        # flag escalates instead, so suppress the per-line price comparison here.
        price_delta = Decimal("0") if currency_mismatch else li.unit_price - po_line.unit_price
        within = (not uom_mismatch) and evaluate_line_tolerance(
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
            status=self._status(within, qty_delta, price_delta, uom_mismatch),
            quantity_delta=qty_delta, price_delta=price_delta, within_tolerance=within,
            received_quantity=grn_line.received_quantity,
            invoiced_to_date_quantity=billed_before,
            remaining_billable_quantity=remaining_billable,
            over_billed=over_billed,
            resolved_sku=resolved_sku,
            alias_unresolved=alias_unresolved,
            uom_mismatch=uom_mismatch,
            note=(
                f"UOM {li.unit_of_measure} ≠ PO {po_line.unit_of_measure} with no conversion"
                if uom_mismatch else None
            ),
        )

    @staticmethod
    def _status(within: bool, qty_delta: Decimal, price_delta: Decimal,
                uom_mismatch: bool = False) -> LineStatus:
        if uom_mismatch:
            return LineStatus.UNIT_VARIANCE
        if within:
            return LineStatus.MATCHED
        if price_delta.copy_abs() > 0:
            return LineStatus.PRICE_VARIANCE
        if qty_delta.copy_abs() > 0:
            return LineStatus.QUANTITY_VARIANCE
        return LineStatus.UNMATCHED
