"""invoice_extractor — turn the source document into a structured VendorInvoice.

Depends only on an :class:`ExtractorPort` (Azure Document Intelligence in prod, a fixture
offline). Extraction failures are returned as an error on the result, never raised.
"""
from __future__ import annotations

from ..envelope import MultiAgentEnvelope, SpecialistResult
from ..ports import ExtractorPort
from ..roles import INVOICE_EXTRACTOR


class InvoiceExtractor:
    role = INVOICE_EXTRACTOR

    def __init__(self, extractor: ExtractorPort) -> None:
        self._extractor = extractor

    def run(self, envelope: MultiAgentEnvelope) -> SpecialistResult:
        try:
            invoice = self._extractor.extract(document_ref=envelope.invoice_ref)
        except Exception as exc:  # noqa: BLE001 — fail-closed, surface as result error
            return SpecialistResult(role=self.role, error=f"extraction failed: {exc}")
        summary = f"Extracted invoice {invoice.invoice_number} from {invoice.vendor_name} " \
                  f"({len(invoice.line_items)} lines, total {invoice.total} {invoice.currency})."
        return SpecialistResult(role=self.role, payload=invoice, summary=summary)
