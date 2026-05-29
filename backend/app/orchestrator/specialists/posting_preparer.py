"""posting_preparer — draft a balanced GL journal from the invoice.

Pure: reads the invoice and the GL account map from the envelope policy. Structure:
AP credit (full total) · per-line expense debits · tax debit. The ``balanced`` flag is set
from the deterministic debit/credit comparison; the authoritative check is re-run by the
reviewer via :func:`check_posting_balance`.
"""
from __future__ import annotations

from decimal import Decimal

from app.schemas.enums import PostingDirection
from app.schemas.money import money_close
from app.schemas.posting import PostingDraft, PostingLine

from ..envelope import MultiAgentEnvelope, SpecialistResult
from ..roles import INVOICE_EXTRACTOR, POSTING_PREPARER


class PostingPreparer:
    role = POSTING_PREPARER

    def run(self, envelope: MultiAgentEnvelope) -> SpecialistResult:
        invoice = envelope.payload_for(INVOICE_EXTRACTOR)
        if invoice is None:
            return SpecialistResult(role=self.role, error="no upstream invoice to post")

        gl = envelope.policy.gl_map
        lines: list[PostingLine] = [
            PostingLine(
                gl_account=gl.ap_liability, direction=PostingDirection.CREDIT,
                amount=invoice.total, memo=f"AP: {invoice.vendor_name} inv {invoice.invoice_number}",
            )
        ]
        for li in invoice.line_items:
            lines.append(PostingLine(
                gl_account=gl.expense_account(li.sku),
                direction=PostingDirection.DEBIT, amount=li.line_total,
                memo=li.description[:80],
            ))
        if invoice.tax_total > 0:
            lines.append(PostingLine(
                gl_account=gl.tax, direction=PostingDirection.DEBIT,
                amount=invoice.tax_total, memo="Input tax",
            ))

        debit = sum((ln.amount for ln in lines if ln.direction is PostingDirection.DEBIT), Decimal("0"))
        credit = sum((ln.amount for ln in lines if ln.direction is PostingDirection.CREDIT), Decimal("0"))
        draft = PostingDraft(
            invoice_number=invoice.invoice_number, currency=invoice.currency,
            lines=lines, balanced=money_close(debit, credit), gl_map_version=gl.version,
        )
        summary = f"Drafted posting: {len(lines)} lines, debit {debit} / credit {credit} " \
                  f"({'balanced' if draft.balanced else 'UNBALANCED'})."
        return SpecialistResult(role=self.role, payload=draft, summary=summary)
