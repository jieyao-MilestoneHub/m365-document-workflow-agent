"""Validation outcome — terminal verdict from the exception_reviewer.

Consistency rule: ``decision == pass`` iff ``blocking_reasons`` is empty.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .deduction import DeductionCase
from .enums import BlockingReason, Decision, Severity


class ExceptionTicket(BaseModel):
    """One row for the human review queue."""

    model_config = ConfigDict(frozen=True)

    ticket_id: str
    exception_type: BlockingReason
    severity: Severity
    affected_lines: list[int] = Field(default_factory=list)
    suggested_resolution: str | None = None
    requires_human: bool = True
    evidence: dict[str, Any] = Field(default_factory=dict)


class ValidationOutcome(BaseModel):
    model_config = ConfigDict(frozen=True)

    invoice_number: str
    decision: Decision
    confidence: float = Field(ge=0.0, le=1.0)
    blocking_reasons: list[BlockingReason] = Field(default_factory=list)
    summary: str = Field(max_length=2000)
    escalation_target: str | None = None
    exception_tickets: list[ExceptionTicket] = Field(default_factory=list)
    #: retail deduction packets for disputable findings (promotion leakage, short receipt)
    deduction_cases: list[DeductionCase] = Field(default_factory=list)
    #: pay-now / hold split: held = Σ deduction amounts, payable = invoice total − held
    payable_amount: Decimal | None = None
    held_amount: Decimal | None = None

    @model_validator(mode="after")
    def _check_consistency(self) -> "ValidationOutcome":
        if self.decision is Decision.PASS and self.blocking_reasons:
            raise ValueError("decision=pass requires empty blocking_reasons")
        if self.decision is not Decision.PASS and not self.blocking_reasons:
            raise ValueError(f"decision={self.decision.value} requires at least one blocking_reason")
        return self
