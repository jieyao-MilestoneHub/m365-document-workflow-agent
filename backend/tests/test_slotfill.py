"""Slot-fill human-in-the-loop: agent pauses on a missing po_ref, asks, then continues."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.adapters.fixtures import FixedClock, ScriptedHumanInput, ScriptedReasoner, SeqIdGen
from app.orchestrator.brain import ScriptedSupervisor
from app.orchestrator.envelope import MultiAgentEnvelope, SpecialistResult
from app.orchestrator.roles import (
    EXCEPTION_REVIEWER,
    INVOICE_EXTRACTOR,
    PO_GRN_MATCHER,
    POSTING_PREPARER,
    VARIANCE_ASSESSOR,
)
from app.orchestrator.specialists.exception_reviewer import ExceptionReviewer
from app.orchestrator.specialists.po_grn_matcher import PoGrnMatcher
from app.orchestrator.specialists.posting_preparer import PostingPreparer
from app.orchestrator.specialists.variance_assessor import VarianceAssessor
from app.orchestrator.supervisor import Supervisor
from app.schemas.enums import BlockingReason, Decision
from app.schemas.invoice import InvoiceLineItem, VendorInvoice
from app.schemas.policy import PolicyBundle
from app.schemas.reference import GoodsReceiptNote, GRNLine, POLine, PurchaseOrder

PO = PurchaseOrder(po_number="PO-5000", vendor_name="Globex", currency="USD",
                   lines=[POLine(sku="WIDGET-A", description="Widget A",
                                 quantity=Decimal("10"), unit_price=Decimal("95.00"))])
GRN = GoodsReceiptNote(grn_number="GRN-7000",
                       lines=[GRNLine(sku="WIDGET-A", description="Widget A",
                                      received_quantity=Decimal("10"))])


class _FixedKnowledge:
    def get_policy(self):
        return PolicyBundle()

    def get_purchase_order(self, *, po_ref):
        return (PO, []) if po_ref == "PO-5000" else (None, [])

    def get_goods_receipt(self, *, grn_ref):
        return (GRN, []) if grn_ref == "GRN-7000" else (None, [])

    def get_invoiced_to_date(self, *, po_ref):
        return {}


class _MissingPoExtractor:
    role = INVOICE_EXTRACTOR

    def __init__(self, invoice):
        self._invoice = invoice

    def run(self, envelope):
        return SpecialistResult(role=self.role, payload=self._invoice)


def _missing_po_invoice() -> VendorInvoice:
    line = InvoiceLineItem(line_no=1, sku="WIDGET-A", description="Widget A",
                           quantity=Decimal("10"), unit_price=Decimal("95.00"),
                           line_total=Decimal("950.00"))
    return VendorInvoice(
        vendor_name="Globex", invoice_number="INV-1057", invoice_date=date(2026, 5, 20),
        currency="USD", subtotal=Decimal("950.00"), tax_total=Decimal("0"), total=Decimal("950.00"),
        po_ref=None, grn_ref="GRN-7000", line_items=[line], missing_fields=["po_ref"],
    )


def _supervisor(human):
    registry = {
        INVOICE_EXTRACTOR: _MissingPoExtractor(_missing_po_invoice()),
        PO_GRN_MATCHER: PoGrnMatcher(_FixedKnowledge()),
        VARIANCE_ASSESSOR: VarianceAssessor(),
        POSTING_PREPARER: PostingPreparer(),
        EXCEPTION_REVIEWER: ExceptionReviewer(ScriptedReasoner()),
    }
    return Supervisor(
        brain=ScriptedSupervisor(), registry=registry, clock=FixedClock(), idgen=SeqIdGen(),
        reasoning=ScriptedReasoner(), human=human,
    )


def _run(human):
    sup = _supervisor(human)
    return sup.run(MultiAgentEnvelope(invoice_ref="INV-1057", policy=PolicyBundle()))


def test_slot_fill_resolves_and_passes():
    result = _run(ScriptedHumanInput({"po_ref": "PO-5000"}))
    assert result.outcome.decision is Decision.PASS
    # the supplied po_ref must clear the exception entirely, not merely flip the verdict
    assert result.outcome.blocking_reasons == []


def test_slot_fill_emits_request_input_event():
    result = _run(ScriptedHumanInput({"po_ref": "PO-5000"}))
    assert any(e.kind == "request_input" for e in result.events)


def test_corrected_invoice_carries_the_supplied_value():
    result = _run(ScriptedHumanInput({"po_ref": "PO-5000"}))
    assert result.envelope.payload_for(INVOICE_EXTRACTOR).po_ref == "PO-5000"


def test_unanswered_slot_falls_back_to_hold():
    result = _run(ScriptedHumanInput({}))  # human cannot answer
    assert result.outcome.decision is Decision.HOLD
    assert BlockingReason.INVOICE_MISSING_FIELDS in result.outcome.blocking_reasons
