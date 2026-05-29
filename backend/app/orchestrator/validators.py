"""Authoritative cross-payload validators.

Each returns a :class:`Verdict`. These run AFTER a specialist emits its payload; a violation
is surfaced to the supervisor, which either retries the specialist or escalates. The LLM
cannot override a violation — this is the Reliability & Safety backbone.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.schemas.enums import BlockingReason
from app.schemas.invoice import VendorInvoice
from app.schemas.money import money_close
from app.schemas.policy import PolicyBundle
from app.schemas.posting import PostingDraft


@dataclass(frozen=True)
class Verdict:
    """Outcome of an authoritative check."""

    ok: bool
    reason: BlockingReason | None = None
    detail: str = ""

    @classmethod
    def passed(cls) -> "Verdict":
        return cls(ok=True)

    @classmethod
    def violation(cls, reason: BlockingReason, detail: str) -> "Verdict":
        return cls(ok=False, reason=reason, detail=detail)


def check_posting_balance(draft: PostingDraft) -> Verdict:
    """Debits must equal credits to the cent."""
    debit, credit = draft.debit_total(), draft.credit_total()
    if not money_close(debit, credit):
        return Verdict.violation(
            BlockingReason.POSTING_DRAFT_UNBALANCED,
            f"debit {debit} != credit {credit}",
        )
    return Verdict.passed()


def check_gl_accounts(draft: PostingDraft, policy: PolicyBundle) -> Verdict:
    """Every posting line must reference a GL account in the chart of accounts.

    Skips the check when no chart-of-accounts allowlist is configured.
    """
    if not policy.valid_gl_accounts:
        return Verdict.passed()
    for line in draft.lines:
        if line.gl_account not in policy.valid_gl_accounts:
            return Verdict.violation(
                BlockingReason.GL_ACCOUNT_INVALID,
                f"GL account {line.gl_account!r} not in chart of accounts",
            )
    return Verdict.passed()


def check_posting_period(invoice: VendorInvoice, policy: PolicyBundle) -> Verdict:
    """The invoice's accounting period (YYYY-MM) must not be closed."""
    period = invoice.invoice_date.strftime("%Y-%m")
    if period in policy.closed_periods:
        return Verdict.violation(
            BlockingReason.POSTING_PERIOD_CLOSED,
            f"period {period} is closed",
        )
    return Verdict.passed()
