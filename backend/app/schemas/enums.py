"""Closed enumerations shared across the three-way-match schemas.

These are intentionally closed sets: the LLM specialists must emit one of these exact
values, and Pydantic rejects anything else — a cheap, authoritative guardrail.
"""
from __future__ import annotations

from enum import Enum


class LineStatus(str, Enum):
    """Per-invoice-line match outcome."""

    MATCHED = "matched"
    QUANTITY_VARIANCE = "quantity_variance"
    PRICE_VARIANCE = "price_variance"
    UNIT_VARIANCE = "unit_variance"
    MISSING_IN_PO = "missing_in_po"
    MISSING_IN_GRN = "missing_in_grn"
    NO_PO_LINE = "no_po_line"
    UNMATCHED = "unmatched"


class LineCharge(str, Enum):
    """What an invoice line represents for posting/matching purposes.

    Only ``good`` lines are subject to three-way match against PO/GRN. Charge lines
    (freight, misc, discount) have no PO/GRN counterpart and are routed/governed separately.
    """

    GOOD = "good"
    FREIGHT = "freight"
    MISC = "misc"
    DISCOUNT = "discount"


class MatchStatus(str, Enum):
    """Roll-up status of the whole three-way match."""

    MATCHED = "matched"
    PARTIAL = "partial"
    MISSING_PO = "missing_po"
    MISSING_GRN = "missing_grn"
    MISMATCH = "mismatch"


class Severity(str, Enum):
    """Variance severity grade."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Decision(str, Enum):
    """Terminal verdict from the exception reviewer / supervisor."""

    PASS = "pass"
    HOLD = "hold"
    ESCALATE = "escalate"


class PostingDirection(str, Enum):
    """GL posting line direction."""

    DEBIT = "debit"
    CREDIT = "credit"


class BlockingReason(str, Enum):
    """Closed set of reasons an invoice cannot auto-post.

    Each value doubles as an exception-ticket type for the review queue.
    """

    # Missing upstream data → escalate
    MISSING_INVOICE_UPSTREAM = "MISSING_INVOICE_UPSTREAM"
    MISSING_THREE_WAY_MATCH_UPSTREAM = "MISSING_THREE_WAY_MATCH_UPSTREAM"
    INVOICE_QUALITY_FAIL = "INVOICE_QUALITY_FAIL"
    # Three-way match
    THREE_WAY_MATCH_INCOMPLETE = "THREE_WAY_MATCH_INCOMPLETE"
    THREE_WAY_MATCH_VARIANCE = "THREE_WAY_MATCH_VARIANCE"
    VARIANCE_HIGH_SEVERITY = "VARIANCE_HIGH_SEVERITY"
    VARIANCE_OUTSIDE_TOLERANCE = "VARIANCE_OUTSIDE_TOLERANCE"
    # Posting / GL
    POSTING_DRAFT_UNBALANCED = "POSTING_DRAFT_UNBALANCED"
    GL_ACCOUNT_INVALID = "GL_ACCOUNT_INVALID"
    POSTING_PERIOD_CLOSED = "POSTING_PERIOD_CLOSED"
    # Vendor policy
    VENDOR_ON_HOLD_LIST = "VENDOR_ON_HOLD_LIST"
    VENDOR_GRAY_ZONE = "VENDOR_GRAY_ZONE"
    # Line-level / data exceptions
    OVER_BILLED_VS_RECEIPT = "OVER_BILLED_VS_RECEIPT"
    UNPLANNED_CHARGE = "UNPLANNED_CHARGE"
    SKU_ALIAS_UNRESOLVED = "SKU_ALIAS_UNRESOLVED"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"
    TAX_DISCREPANCY = "TAX_DISCREPANCY"
    # Quality warnings
    INVOICE_QUALITY_WARN = "INVOICE_QUALITY_WARN"
    INVOICE_MISSING_FIELDS = "INVOICE_MISSING_FIELDS"
    # Orchestration-level failures
    SUPERVISOR_GUARDRAIL_VETO = "SUPERVISOR_GUARDRAIL_VETO"
    SPECIALIST_FAILED = "SPECIALIST_FAILED"


#: Blocking reasons that force an escalate (vs a hold).
ESCALATE_REASONS: frozenset[BlockingReason] = frozenset(
    {
        BlockingReason.MISSING_INVOICE_UPSTREAM,
        BlockingReason.MISSING_THREE_WAY_MATCH_UPSTREAM,
        BlockingReason.INVOICE_QUALITY_FAIL,
        BlockingReason.VARIANCE_HIGH_SEVERITY,
        BlockingReason.POSTING_DRAFT_UNBALANCED,
        BlockingReason.GL_ACCOUNT_INVALID,
        BlockingReason.POSTING_PERIOD_CLOSED,
        BlockingReason.SUPERVISOR_GUARDRAIL_VETO,
        BlockingReason.SPECIALIST_FAILED,
        BlockingReason.CURRENCY_MISMATCH,
        BlockingReason.DUPLICATE_INVOICE,
    }
)
