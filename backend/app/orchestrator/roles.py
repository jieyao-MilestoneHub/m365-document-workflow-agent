"""Specialist role names and their natural dependency order.

Centralized so there are no magic strings; the supervisor routes over the registry, and new
roles can be added without touching the supervisor loop (Open/Closed).
"""
from __future__ import annotations

SUPERVISOR = "supervisor"
INVOICE_EXTRACTOR = "invoice_extractor"
PO_GRN_MATCHER = "po_grn_matcher"
VARIANCE_ASSESSOR = "variance_assessor"
POSTING_PREPARER = "posting_preparer"
EXCEPTION_REVIEWER = "exception_reviewer"

#: dependency order — each role consumes the outputs of those before it
PIPELINE_ORDER: tuple[str, ...] = (
    INVOICE_EXTRACTOR,
    PO_GRN_MATCHER,
    VARIANCE_ASSESSOR,
    POSTING_PREPARER,
    EXCEPTION_REVIEWER,
)
