"""Pure matching and variance math.

These functions are deterministic and side-effect free. Specialists call them so the
arithmetic of tolerance, severity, and status roll-up is identical every run — the LLM only
decides fuzzy questions (which PO line corresponds to a description), never the numbers.
"""
from __future__ import annotations

from decimal import Decimal

from app.schemas.enums import MatchStatus, Severity
from app.schemas.policy import TolerancePolicy, VarianceThresholds


def evaluate_line_tolerance(
    *,
    quantity_delta: Decimal,
    price_delta: Decimal,
    po_unit_price: Decimal,
    tolerance: TolerancePolicy,
) -> bool:
    """True when a line's quantity and price deltas are both within tolerance.

    ``within = |Δqty| ≤ qty_absolute  AND  |Δprice| ≤ max(price_absolute, price_percent×PO)``.
    """
    qty_ok = quantity_delta.copy_abs() <= tolerance.quantity_absolute
    price_ok = price_delta.copy_abs() <= tolerance.price_limit(po_unit_price)
    return qty_ok and price_ok


def grade_severity(financial_impact: Decimal, thresholds: VarianceThresholds) -> Severity:
    """Grade a financial impact into a severity bucket.

    Non-zero impact is never ``none`` — even a tiny variance is at least ``low``.
    """
    impact = financial_impact.copy_abs()
    if impact >= thresholds.high_threshold:
        return Severity.HIGH
    if impact >= thresholds.medium_threshold:
        return Severity.MEDIUM
    if impact > 0:
        return Severity.LOW
    return Severity.NONE


#: severity ordering for "overall = max" roll-ups
_SEVERITY_ORDER = {Severity.NONE: 0, Severity.LOW: 1, Severity.MEDIUM: 2, Severity.HIGH: 3}


def max_severity(severities: list[Severity]) -> Severity:
    """Return the highest severity in a list (``none`` if empty)."""
    if not severities:
        return Severity.NONE
    return max(severities, key=lambda s: _SEVERITY_ORDER[s])


def roll_up_match_status(
    *,
    has_line_items: bool,
    po_present: bool,
    grn_present: bool,
    all_lines_matched: bool,
    all_within_tolerance: bool,
) -> MatchStatus:
    """Derive the overall match status from per-line outcomes and reference availability."""
    if not has_line_items:
        return MatchStatus.MISMATCH
    if not po_present:
        return MatchStatus.MISSING_PO
    if not grn_present:
        return MatchStatus.MISSING_GRN
    if all_lines_matched and all_within_tolerance:
        return MatchStatus.MATCHED
    return MatchStatus.PARTIAL
