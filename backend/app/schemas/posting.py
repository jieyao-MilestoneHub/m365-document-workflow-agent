"""GL posting draft — output of the posting_preparer specialist.

The ``balanced`` flag is advisory; the authoritative balance check lives in
``orchestrator.validators.check_posting_balance`` and the exception_reviewer trusts that.
"""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from .enums import PostingDirection


class PostingLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    gl_account: str = Field(min_length=1)
    direction: PostingDirection
    amount: Decimal = Field(gt=0, description="always positive; direction carries the sign")
    memo: str | None = Field(default=None, max_length=256)


class PostingDraft(BaseModel):
    model_config = ConfigDict(frozen=True)

    invoice_number: str
    currency: str = Field(min_length=3, max_length=3)
    lines: list[PostingLine] = Field(default_factory=list)
    balanced: bool = False
    notes: list[str] = Field(default_factory=list)
    gl_map_version: str = "ap.gl.v1"

    def debit_total(self) -> Decimal:
        return sum(
            (ln.amount for ln in self.lines if ln.direction is PostingDirection.DEBIT),
            Decimal("0"),
        )

    def credit_total(self) -> Decimal:
        return sum(
            (ln.amount for ln in self.lines if ln.direction is PostingDirection.CREDIT),
            Decimal("0"),
        )
