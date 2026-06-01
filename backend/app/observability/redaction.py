"""Redaction filter — adapt :mod:`redactkit` for stdlib :mod:`logging`.

Why an adapter at the logger layer rather than at call sites: handlers and third-party
libraries (uvicorn, the Azure Monitor exporter, FastAPI access logs) all emit
:class:`logging.LogRecord` objects through the root logger. A single
:class:`logging.Filter` attached once at startup catches them uniformly (Open/Closed —
existing handlers gain redaction without modification).

Invoice domain coverage: redactkit's built-ins are key-pattern based (``password=``,
``token=``, ...) and do not natively detect free-form vendor names, tax IDs, or monetary
amounts. We supplement with two regex stopgaps below; the upstream gap is tracked at
https://github.com/CoreNovus/redactkit/issues so the local code can be deleted once
detectors ship.
"""
from __future__ import annotations

import logging
import re
from typing import Any

try:
    from redactkit import extend_key_pattern, redact_text
except ImportError:  # pragma: no cover - exercised via the fallback path
    extend_key_pattern = None  # type: ignore[assignment]
    redact_text = None  # type: ignore[assignment]


# Invoice-domain stopgaps (local, ≤ 20 lines, deletable once redactkit ships detectors).
_MONEY_RE = re.compile(r"[\$£€¥]\s?\d[\d,]*(?:\.\d{1,4})?")
_TAX_ID_RE = re.compile(r"\b(?:VAT|EIN|GSTIN|ABN|GST)\s?[A-Z]{0,3}\d{6,}\b", re.IGNORECASE)

#: Extra key-pattern terms passed to redactkit for invoice-specific keys.
_INVOICE_KEY_TERMS = ("vendor_name", "tax_id", "invoice_ref", "invoice_number")

_KEY_PATTERN: Any | None = None
if extend_key_pattern is not None:
    _KEY_PATTERN = extend_key_pattern(list(_INVOICE_KEY_TERMS))


def _mask_invoice_fields(text: str) -> str:
    text = _TAX_ID_RE.sub("[REDACTED_TAX_ID]", text)
    text = _MONEY_RE.sub("[REDACTED_AMOUNT]", text)
    return text


def redact(text: str) -> str:
    """Apply redactkit key-pattern redaction + invoice stopgap masks. Safe on any string."""
    if redact_text is None:
        return _mask_invoice_fields(text)
    try:
        return _mask_invoice_fields(redact_text(text, key_pattern=_KEY_PATTERN))
    except Exception:  # pragma: no cover - redaction must NEVER break logging
        return text


class RedactingFilter(logging.Filter):
    """Apply :func:`redact` to ``record.msg`` and its formatting args."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = redact(str(record.msg))
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {k: redact(str(v)) for k, v in record.args.items()}
                else:
                    record.args = tuple(redact(str(a)) for a in record.args)
        except Exception:  # pragma: no cover - belt-and-suspenders
            pass
        return True
