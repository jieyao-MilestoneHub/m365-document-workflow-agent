"""Offline, deterministic port implementations backed by synthetic JSON in ``sample-data/``.

These are first-class (not throwaway): they let the entire agentic pipeline run and be tested
with zero cloud credentials, and they document the exact data shapes the Azure adapters must
produce.
"""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from app.schemas.citation import Citation
from app.schemas.invoice import VendorInvoice
from app.schemas.policy import PolicyBundle
from app.schemas.reference import GoodsReceiptNote, PurchaseOrder


class FixtureExtractor:
    """ExtractorPort backed by ``<base>/invoices/<ref>.json``."""

    def __init__(self, base_dir: str | Path) -> None:
        self._base = Path(base_dir)

    def extract(self, *, document_ref: str) -> VendorInvoice:
        path = self._base / "invoices" / f"{document_ref}.json"
        if not path.exists():
            raise FileNotFoundError(f"no fixture invoice for {document_ref!r}")
        return VendorInvoice.model_validate_json(path.read_text(encoding="utf-8"))


class FixtureKnowledge:
    """KnowledgePort backed by ``<base>/{policy,purchase_orders,goods_receipts}``."""

    def __init__(self, base_dir: str | Path) -> None:
        self._base = Path(base_dir)

    def get_policy(self) -> PolicyBundle:
        path = self._base / "policy.json"
        if path.exists():
            return PolicyBundle.model_validate_json(path.read_text(encoding="utf-8"))
        return PolicyBundle()

    def get_purchase_order(self, *, po_ref: str | None):
        if not po_ref:
            return None, []
        path = self._base / "purchase_orders" / f"{po_ref}.json"
        if not path.exists():
            return None, []
        po = PurchaseOrder.model_validate_json(path.read_text(encoding="utf-8"))
        return po, [self._citation(po_ref, "Purchase Order", _po_snippet(po))]

    def get_goods_receipt(self, *, grn_ref: str | None):
        if not grn_ref:
            return None, []
        path = self._base / "goods_receipts" / f"{grn_ref}.json"
        if not path.exists():
            return None, []
        grn = GoodsReceiptNote.model_validate_json(path.read_text(encoding="utf-8"))
        return grn, [self._citation(grn_ref, "Goods Receipt Note", _grn_snippet(grn))]

    def get_invoiced_to_date(self, *, po_ref: str | None) -> dict:
        if not po_ref:
            return {}
        path = self._base / "invoiced_to_date.json"
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return {k: Decimal(str(v)) for k, v in data.get(po_ref, {}).items()}

    @staticmethod
    def _citation(doc_id: str, kind: str, snippet: str) -> Citation:
        return Citation(document_id=doc_id, document_title=f"{kind} {doc_id}", cited_text=snippet)


def _po_snippet(po: PurchaseOrder) -> str:
    return "; ".join(f"{ln.sku or ln.description} x{ln.quantity} @ {ln.unit_price}" for ln in po.lines)


def _grn_snippet(grn: GoodsReceiptNote) -> str:
    return "; ".join(f"{ln.sku or ln.description} received {ln.received_quantity}" for ln in grn.lines)


class FixtureLedger:
    """LedgerPort backed by ``<base>/posted_ledger.json`` (a list of {vendor_name, invoice_number})."""

    def __init__(self, base_dir: str | Path) -> None:
        self._base = Path(base_dir)

    def seen_invoice(self, *, vendor_name: str, invoice_number: str) -> bool:
        path = self._base / "posted_ledger.json"
        if not path.exists():
            return False
        entries = json.loads(path.read_text(encoding="utf-8"))
        return any(
            e.get("vendor_name") == vendor_name and e.get("invoice_number") == invoice_number
            for e in entries
        )


class FixedClock:
    """Deterministic clock for reproducible traces/tests."""

    def __init__(self, value: str = "2026-05-29T00:00:00Z") -> None:
        self._value = value

    def now_iso(self) -> str:
        return self._value


class SeqIdGen:
    """Deterministic sequential id generator."""

    def __init__(self, prefix: str = "evt") -> None:
        self._n = 0
        self._prefix = prefix

    def next_id(self) -> str:
        self._n += 1
        return f"{self._prefix}-{self._n:04d}"


class ScriptedReasoner:
    """Deterministic narration stand-in for an LLM ReasoningPort."""

    def narrate(self, *, role: str, context: dict) -> str:
        if "decision" in context:
            reasons = context.get("blocking_reasons") or []
            tail = "; ".join(reasons) if reasons else "clean three-way match, ready to post"
            return f"{context['decision'].title()} - {tail}."
        if "subject" in context:
            return f"Peer review of {context['subject']}: accept - grading consistent with deltas."
        return f"{role}: ok."
