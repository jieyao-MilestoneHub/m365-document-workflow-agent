from datetime import date
from decimal import Decimal

from app.orchestrator.validators import (
    check_gl_accounts,
    check_posting_balance,
    check_posting_period,
)
from app.schemas.enums import BlockingReason
from app.schemas.policy import PolicyBundle

from .conftest import balanced_posting, unbalanced_posting


def test_balanced_posting_passes():
    assert check_posting_balance(balanced_posting()).ok is True


def test_unbalanced_posting_flags_reason():
    verdict = check_posting_balance(unbalanced_posting())
    assert verdict.reason is BlockingReason.POSTING_DRAFT_UNBALANCED


def test_gl_check_skipped_without_allowlist():
    assert check_gl_accounts(balanced_posting(), PolicyBundle()).ok is True


def test_gl_check_flags_unknown_account():
    policy = PolicyBundle(valid_gl_accounts=frozenset({"2100"}))  # 5000 missing
    verdict = check_gl_accounts(balanced_posting(), policy)
    assert verdict.reason is BlockingReason.GL_ACCOUNT_INVALID


def test_closed_period_flagged(clean_invoice):
    policy = PolicyBundle(closed_periods=frozenset({"2026-05"}))
    verdict = check_posting_period(clean_invoice, policy)
    assert verdict.reason is BlockingReason.POSTING_PERIOD_CLOSED


def test_open_period_passes(clean_invoice):
    assert check_posting_period(clean_invoice, PolicyBundle()).ok is True
