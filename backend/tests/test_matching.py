from decimal import Decimal

from app.orchestrator.matching import (
    evaluate_line_tolerance,
    grade_severity,
    max_severity,
    roll_up_match_status,
)
from app.schemas.enums import MatchStatus, Severity
from app.schemas.policy import TolerancePolicy, VarianceThresholds

TOL = TolerancePolicy()
TH = VarianceThresholds()


def test_price_within_percent_tolerance_passes():
    # 1% of a 100.00 unit price = 1.00 allowance; delta 0.80 is within.
    assert evaluate_line_tolerance(
        quantity_delta=Decimal("0"), price_delta=Decimal("0.80"),
        po_unit_price=Decimal("100.00"), tolerance=TOL,
    ) is True


def test_price_beyond_percent_tolerance_fails():
    # 2% of 100.00 = 2.00 allowance; delta 6.00 (a +6% bill) is outside.
    assert evaluate_line_tolerance(
        quantity_delta=Decimal("0"), price_delta=Decimal("6.00"),
        po_unit_price=Decimal("100.00"), tolerance=TOL,
    ) is False


def test_quantity_beyond_absolute_tolerance_fails():
    assert evaluate_line_tolerance(
        quantity_delta=Decimal("1.0"), price_delta=Decimal("0"),
        po_unit_price=Decimal("10.00"), tolerance=TOL,
    ) is False


def test_grade_severity_high_at_threshold():
    assert grade_severity(Decimal("500.00"), TH) is Severity.HIGH


def test_grade_severity_low_for_small_nonzero_impact():
    assert grade_severity(Decimal("0.01"), TH) is Severity.LOW


def test_grade_severity_none_for_zero():
    assert grade_severity(Decimal("0"), TH) is Severity.NONE


def test_max_severity_picks_highest():
    assert max_severity([Severity.LOW, Severity.HIGH, Severity.MEDIUM]) is Severity.HIGH


def test_roll_up_matched_when_all_within_tolerance():
    assert roll_up_match_status(
        has_line_items=True, po_present=True, grn_present=True,
        all_lines_matched=True, all_within_tolerance=True,
    ) is MatchStatus.MATCHED


def test_roll_up_partial_when_a_line_out_of_tolerance():
    assert roll_up_match_status(
        has_line_items=True, po_present=True, grn_present=True,
        all_lines_matched=True, all_within_tolerance=False,
    ) is MatchStatus.PARTIAL


def test_roll_up_missing_po():
    assert roll_up_match_status(
        has_line_items=True, po_present=False, grn_present=True,
        all_lines_matched=False, all_within_tolerance=False,
    ) is MatchStatus.MISSING_PO
