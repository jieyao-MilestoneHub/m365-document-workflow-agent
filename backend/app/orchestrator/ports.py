"""Port protocols — the abstractions the orchestrator depends on (Dependency Inversion).

Specialists and the supervisor depend ONLY on these narrow interfaces, never on concrete
Azure SDKs. Each port has a Fixture/Scripted implementation (offline: tests + CLI) and an
Azure implementation (prod) under ``app/adapters`` — fully substitutable (Liskov).
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Protocol, runtime_checkable

from app.schemas.citation import Citation
from app.schemas.invoice import VendorInvoice
from app.schemas.policy import PolicyBundle
from app.schemas.promotion import Promotion
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

    def get_promotions(
        self, *, vendor_name: str, po_ref: str | None, invoice_date: date
    ) -> tuple[list[Promotion], list[Citation]]:
        """Trade-promotion agreements in effect for this vendor on the invoice date.

        Returns the applicable promotions plus a citation per promotion (the agreement is the
        grounded evidence behind a missing-allowance deduction).
        """
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
class HumanInputPort(Protocol):
    """Ask a human to supply a missing field (Copilot adaptive card in prod; scripted offline).

    Returns the answer, or None if it cannot be resolved (the run then holds for review).
    """

    def answer(self, *, field: str, prompt: str, candidates: list[str]) -> str | None: ...


@runtime_checkable
class Clock(Protocol):
    """Injected time source (keeps logic deterministic and testable)."""

    def now_iso(self) -> str: ...

    def monotonic(self) -> float:
        """Monotonic seconds for latency measurement.

        ``now_iso`` returns a wall-clock string and is unsuitable for measuring duration
        (NTP corrections can move wall clocks backwards). This separate clock yields a
        strictly non-decreasing float per call.
        """
        ...


@runtime_checkable
class IdGen(Protocol):
    """Injected id source (keeps logic deterministic and testable)."""

    def next_id(self) -> str: ...
