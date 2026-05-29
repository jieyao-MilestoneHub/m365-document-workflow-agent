"""Variance report — output of the variance_assessor specialist.

Severity tracks absolute financial impact regardless of sign; a line with non-zero impact
is never graded ``none``.
"""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from .enums import Severity


class LineVariance(BaseModel):
    model_config = ConfigDict(frozen=True)

    invoice_line_no: int
    financial_impact: Decimal = Field(ge=0)
    severity: Severity
    within_tolerance: bool
    rationale: str | None = None


class VarianceReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    invoice_number: str
    lines: list[LineVariance] = Field(default_factory=list)
    overall_severity: Severity = Severity.NONE
    financial_impact_total: Decimal = Field(default=Decimal("0"), ge=0)
    thresholds_version: str = "2026.04.1"
