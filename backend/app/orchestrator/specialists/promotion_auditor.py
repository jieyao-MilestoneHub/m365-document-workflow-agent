"""promotion_auditor — reconcile the invoice against its trade-promotion agreements.

This is the retail differentiator. A three-way match only checks PO ↔ GRN ↔ invoice; the
commercial condition (a promotion allowance the supplier owes) lives outside that triad. This
specialist fetches the promotions in effect for the vendor on the invoice date (grounded, with
citations, via the :class:`KnowledgePort`) and computes, per promotion:

    expected = Σ(billed qty for the promo SKU) × allowance_per_unit
    applied  = Σ invoice.allowances credited for that promotion
    leakage  = max(0, expected − applied)

It emits an :class:`AllowanceAudit` payload only — the verdict (HOLD on leakage) is the
deterministic decision matrix's job, never the LLM's.
"""
from __future__ import annotations

from decimal import Decimal

from app.schemas.deduction import AllowanceAudit, AllowanceLine
from app.schemas.enums import LineCharge
from app.schemas.invoice import VendorInvoice
from app.schemas.promotion import Promotion

from ..envelope import MultiAgentEnvelope, SpecialistResult
from ..ports import KnowledgePort
from ..roles import INVOICE_EXTRACTOR, PROMOTION_AUDITOR


class PromotionAuditor:
    role = PROMOTION_AUDITOR

    def __init__(self, knowledge: KnowledgePort) -> None:
        self._knowledge = knowledge

    def run(self, envelope: MultiAgentEnvelope) -> SpecialistResult:
        invoice: VendorInvoice | None = envelope.payload_for(INVOICE_EXTRACTOR)
        if invoice is None:
            return SpecialistResult(role=self.role, error="no upstream invoice to audit")

        promotions, citations = self._knowledge.get_promotions(
            vendor_name=invoice.vendor_name,
            po_ref=invoice.po_ref,
            invoice_date=invoice.invoice_date,
        )
        lines = [self._reconcile(invoice, promo) for promo in promotions]
        leakage_total = sum((ln.leakage for ln in lines), Decimal("0"))
        audit = AllowanceAudit(
            invoice_number=invoice.invoice_number,
            lines=lines,
            margin_leakage_total=leakage_total,
            applicable_promotions=list(promotions),
            citations=list(citations),
        )
        if not promotions:
            summary = "Allowance audit: no promotions in effect; nothing to reconcile."
        else:
            summary = (
                f"Allowance audit: {len(promotions)} promotion(s) in effect, "
                f"margin leakage {leakage_total}."
            )
        return SpecialistResult(
            role=self.role, payload=audit, citations=tuple(citations), summary=summary
        )

    @staticmethod
    def _reconcile(invoice: VendorInvoice, promo: Promotion) -> AllowanceLine:
        matched = [
            li for li in invoice.line_items
            if li.charge_type is LineCharge.GOOD and (promo.sku is None or li.sku == promo.sku)
        ]
        billed_qty = sum((li.quantity for li in matched), Decimal("0"))
        expected = billed_qty * promo.allowance_per_unit
        applied = sum(
            (
                a.amount for a in invoice.allowances
                if a.promo_id == promo.promo_id
                or (a.promo_id is None and a.sku is not None and a.sku == promo.sku)
            ),
            Decimal("0"),
        )
        leakage = expected - applied
        if leakage < 0:
            leakage = Decimal("0")
        return AllowanceLine(
            promo_id=promo.promo_id,
            sku=promo.sku,
            billed_quantity=billed_qty,
            expected_allowance=expected,
            applied_allowance=applied,
            leakage=leakage,
            affected_lines=[li.line_no for li in matched],
        )
