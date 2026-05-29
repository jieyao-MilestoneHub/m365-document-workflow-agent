"""variance_assessor — grade the financial impact and severity of each mismatched line.

Pure: reads the invoice and match report from the envelope plus the policy thresholds.
Trusts the matcher's deltas (does not re-match) and uses :func:`grade_severity`.
"""
from __future__ import annotations

from decimal import Decimal

from app.schemas.enums import LineStatus, Severity
from app.schemas.match import ThreeWayMatchReport
from app.schemas.variance import LineVariance, VarianceReport

from ..envelope import MultiAgentEnvelope, SpecialistResult
from ..matching import grade_severity, max_severity
from ..roles import INVOICE_EXTRACTOR, PO_GRN_MATCHER, VARIANCE_ASSESSOR


class VarianceAssessor:
    role = VARIANCE_ASSESSOR

    def run(self, envelope: MultiAgentEnvelope) -> SpecialistResult:
        invoice = envelope.payload_for(INVOICE_EXTRACTOR)
        report: ThreeWayMatchReport | None = envelope.payload_for(PO_GRN_MATCHER)
        if invoice is None or report is None:
            return SpecialistResult(role=self.role, error="missing upstream invoice or match report")

        thresholds = envelope.policy.thresholds
        qty_by_line = {li.line_no: li.quantity for li in invoice.line_items}
        lines: list[LineVariance] = []
        for m in report.lines:
            if m.status is LineStatus.MATCHED:
                continue
            impact = self._impact(m, qty_by_line.get(m.invoice_line_no, Decimal("0")))
            lines.append(LineVariance(
                invoice_line_no=m.invoice_line_no,
                financial_impact=impact,
                severity=grade_severity(impact, thresholds),
                within_tolerance=m.within_tolerance,
                rationale=f"{m.status.value}: qtyΔ={m.quantity_delta}, priceΔ={m.price_delta}",
            ))

        overall = max_severity([lv.severity for lv in lines])
        total = sum((lv.financial_impact for lv in lines), Decimal("0"))
        result = VarianceReport(
            invoice_number=invoice.invoice_number, lines=lines,
            overall_severity=overall, financial_impact_total=total,
            thresholds_version=thresholds.version,
        )
        summary = f"Variance: {len(lines)} line(s) off, overall {overall.value}, impact {total}."
        return SpecialistResult(role=self.role, payload=result, summary=summary)

    @staticmethod
    def _impact(line_match, invoice_qty: Decimal) -> Decimal:
        # price variance: |Δprice| × invoice qty; quantity variance: |Δqty| × PO unit price.
        if line_match.price_delta.copy_abs() > 0:
            return line_match.price_delta.copy_abs() * invoice_qty
        if line_match.quantity_delta.copy_abs() > 0:
            po_unit = line_match.po_unit_price or Decimal("0")
            return line_match.quantity_delta.copy_abs() * po_unit
        return Decimal("0")
