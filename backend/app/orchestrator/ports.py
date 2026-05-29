"""Port protocols — the abstractions the orchestrator depends on (Dependency Inversion).

Specialists and the supervisor depend ONLY on these narrow interfaces, never on concrete
Azure SDKs. Each port has a Fixture/Scripted implementation (offline: tests + CLI) and an
Azure implementation (prod) under ``app/adapters`` — fully substitutable (Liskov).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Protocol, runtime_checkable

from app.schemas.citation import Citation
from app.schemas.invoice import VendorInvoice
from app.schemas.policy import PolicyBundle
from app.schemas.reference import GoodsReceiptNote, PurchaseOrder


@runtime_checkable
class ExtractorPort(Protocol):
    """Turn a source document into a structured invoice (e.g. Azure Document Intelligence)."""

    def extract(self, *, document_ref: str) -> VendorInvoice: ...


@runtime_checkable
class KnowledgePort(Protocol):
    """Grounded retrieval of reference data with citations (e.g. Foundry IQ)."""

    def get_policy(self) -> PolicyBundle: ...

    def get_purchase_order(
        self, *, po_ref: str | None
    ) -> tuple[PurchaseOrder | None, list[Citation]]: ...

    def get_goods_receipt(
        self, *, grn_ref: str | None
    ) -> tuple[GoodsReceiptNote | None, list[Citation]]: ...

    def get_invoiced_to_date(self, *, po_ref: str | None) -> dict[str, Decimal]:
        """Quantity already invoiced per line key (sku or description) against this PO."""
        ...


@runtime_checkable
class LedgerPort(Protocol):
    """Check whether an invoice was already posted (duplicate-payment control)."""

    def seen_invoice(self, *, vendor_name: str, invoice_number: str) -> bool: ...


@runtime_checkable
class ReasoningPort(Protocol):
    """Produce a short natural-language rationale for a step (e.g. Azure OpenAI).

    The reasoning text is advisory narration only — it never decides outcomes, which remain
    the job of the deterministic guardrails and decision matrix.
    """

    def narrate(self, *, role: str, context: dict) -> str: ...


@runtime_checkable
class Clock(Protocol):
    """Injected time source (keeps logic deterministic and testable)."""

    def now_iso(self) -> str: ...


@runtime_checkable
class IdGen(Protocol):
    """Injected id source (keeps logic deterministic and testable)."""

    def next_id(self) -> str: ...
