"""Typed contracts for the three-way-match workflow.

These Pydantic models are the interface between specialists and the authoritative guardrails
in :mod:`app.orchestrator.validators`. Money is always :class:`decimal.Decimal`.
"""
from __future__ import annotations

from .citation import Citation
from .enums import (
    ESCALATE_REASONS,
    BlockingReason,
    Decision,
    LineStatus,
    MatchStatus,
    PostingDirection,
    Severity,
)
from .invoice import InvoiceLineItem, VendorInvoice
from .match import LineMatch, ThreeWayMatchReport
from .money import CENTS, money_close, to_money
from .outcome import ExceptionTicket, ValidationOutcome
from .policy import GLMap, PolicyBundle, TolerancePolicy, VarianceThresholds, VendorConfig
from .posting import PostingDraft, PostingLine
from .reference import GoodsReceiptNote, GRNLine, POLine, PurchaseOrder
from .variance import LineVariance, VarianceReport

__all__ = [
    "CENTS",
    "ESCALATE_REASONS",
    "BlockingReason",
    "Citation",
    "Decision",
    "ExceptionTicket",
    "GLMap",
    "GRNLine",
    "GoodsReceiptNote",
    "InvoiceLineItem",
    "LineMatch",
    "LineStatus",
    "LineVariance",
    "MatchStatus",
    "POLine",
    "PolicyBundle",
    "PostingDirection",
    "PostingDraft",
    "PostingLine",
    "PurchaseOrder",
    "Severity",
    "ThreeWayMatchReport",
    "TolerancePolicy",
    "ValidationOutcome",
    "VarianceReport",
    "VarianceThresholds",
    "VendorConfig",
    "VendorInvoice",
    "money_close",
    "to_money",
]
