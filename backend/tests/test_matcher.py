"""Matcher unit tests with an in-memory KnowledgePort (no fixtures on disk)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.orchestrator.envelope import MultiAgentEnvelope, SpecialistResult
from app.orchestrator.roles import INVOICE_EXTRACTOR
from app.orchestrator.specialists.po_grn_matcher import PoGrnMatcher
from app.schemas.enums import LineStatus
from app.schemas.invoice import InvoiceLineItem, VendorInvoice
from app.schemas.policy import PolicyBundle
from app.schemas.reference import GoodsReceiptNote, GRNLine, POLine, PurchaseOrder


class _FakeKnowledge:
    def __init__(self, po, grn, invoiced=None):
        self._po, self._grn, self._invoiced = po, grn, invoiced or {}

    def get_policy(self):  # not used by the matcher (policy comes from the envelope)
        return PolicyBundle()

    def get_purchase_order(self, *, po_ref):
        return self._po, []

    def get_goods_receipt(self, *, grn_ref):
        return self._grn, []

    def get_invoiced_to_date(self, *, po_ref):
        return self._invoiced


def _invoice(qty: str, sku: str = "WIDGET-A") -> VendorInvoice:
    line = InvoiceLineItem(
        line_no=1, sku=sku, description="Widget A", quantity=Decimal(qty),
        unit_price=Decimal("95.00"), line_total=Decimal(qty) * Decimal("95.00"),
    )
    return VendorInvoice(
        vendor_name="Globex", invoice_number="INV-X", invoice_date=date(2026, 5, 20),
        currency="USD", subtotal=line.line_total, tax_total=Decimal("0"), total=line.line_total,
        po_ref="PO-5000", grn_ref="GRN-7000", line_items=[line],
    )


def _envelope(invoice, policy: PolicyBundle | None = None) -> MultiAgentEnvelope:
    env = MultiAgentEnvelope(invoice_ref=invoice.invoice_number, policy=policy or PolicyBundle())
    return env.with_result(SpecialistResult(role=INVOICE_EXTRACTOR, payload=invoice))


_FULL_GRN = GoodsReceiptNote(grn_number="GRN-7000",
                             lines=[GRNLine(sku="WIDGET-A", description="Widget A",
                                            received_quantity=Decimal("10"))])


PO = PurchaseOrder(po_number="PO-5000", vendor_name="Globex", currency="USD",
                   lines=[POLine(sku="WIDGET-A", description="Widget A",
                                 quantity=Decimal("10"), unit_price=Decimal("95.00"))])


def test_over_billed_when_billed_exceeds_received():
    grn = GoodsReceiptNote(grn_number="GRN-7000",
                           lines=[GRNLine(sku="WIDGET-A", description="Widget A",
                                          received_quantity=Decimal("6"))])
    matcher = PoGrnMatcher(_FakeKnowledge(PO, grn))
    report = matcher.run(_envelope(_invoice("10"))).payload
    line = report.lines[0]
    assert line.over_billed is True
    assert line.remaining_billable_quantity == Decimal("6")


def test_not_over_billed_when_within_receipt():
    grn = GoodsReceiptNote(grn_number="GRN-7000",
                           lines=[GRNLine(sku="WIDGET-A", description="Widget A",
                                          received_quantity=Decimal("10"))])
    matcher = PoGrnMatcher(_FakeKnowledge(PO, grn))
    report = matcher.run(_envelope(_invoice("10"))).payload
    assert report.lines[0].over_billed is False


def test_over_billed_accounts_for_prior_invoicing():
    grn = GoodsReceiptNote(grn_number="GRN-7000",
                           lines=[GRNLine(sku="WIDGET-A", description="Widget A",
                                          received_quantity=Decimal("10"))])
    # 8 already billed → only 2 remain billable, so billing 10 over-bills
    matcher = PoGrnMatcher(_FakeKnowledge(PO, grn, {"WIDGET-A": Decimal("8")}))
    report = matcher.run(_envelope(_invoice("10"))).payload
    assert report.lines[0].over_billed is True
    assert report.lines[0].remaining_billable_quantity == Decimal("2")


def test_vendor_sku_resolves_via_alias():
    policy = PolicyBundle(sku_aliases={"GLX-WA-01": "WIDGET-A"})
    matcher = PoGrnMatcher(_FakeKnowledge(PO, _FULL_GRN))
    report = matcher.run(_envelope(_invoice("10", sku="GLX-WA-01"), policy)).payload
    line = report.lines[0]
    assert line.resolved_sku == "WIDGET-A"
    assert line.alias_unresolved is False
    assert line.status is LineStatus.MATCHED


def test_unknown_vendor_sku_flags_alias_unresolved():
    # no alias for UNKNOWN-X; only the description rescues the match → needs human confirm
    matcher = PoGrnMatcher(_FakeKnowledge(PO, _FULL_GRN))
    report = matcher.run(_envelope(_invoice("10", sku="UNKNOWN-X"))).payload
    assert report.lines[0].alias_unresolved is True
