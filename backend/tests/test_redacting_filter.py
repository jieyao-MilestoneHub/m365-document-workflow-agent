"""RedactingFilter — must mask common secrets and invoice-domain fields."""
from __future__ import annotations

import logging

import pytest

from app.observability.redaction import RedactingFilter, redact


def test_mask_password_via_redactkit():
    pytest.importorskip("redactkit")
    out = redact("password=hunter2 user=alice")
    assert "hunter2" not in out
    assert "user=alice" in out


def test_mask_invoice_tax_id():
    out = redact("contact alice@acme.com VAT GB123456789 paid")
    assert "GB123456789" not in out
    assert "[REDACTED_TAX_ID]" in out


def test_mask_money_amount():
    out = redact("total $1,234.56 due")
    assert "$1,234.56" not in out
    assert "[REDACTED_AMOUNT]" in out


def test_mask_extended_invoice_keys():
    pytest.importorskip("redactkit")
    out = redact("vendor_name=Globex tax_id=GB123456789 other=ok")
    assert "Globex" not in out
    assert "GB123456789" not in out
    assert "other=ok" in out


def test_filter_applies_to_log_record_msg_and_args():
    flt = RedactingFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="x.py",
        lineno=1,
        msg="password=topsecret total $99.00",
        args=(),
        exc_info=None,
    )
    assert flt.filter(record) is True
    assert "topsecret" not in str(record.msg)
    assert "$99.00" not in str(record.msg)


def test_filter_handles_tuple_args():
    flt = RedactingFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="x.py",
        lineno=1,
        msg="vendor %s total %s",
        args=("vendor_name=Globex", "$99.00"),
        exc_info=None,
    )
    assert flt.filter(record) is True
    assert "$99.00" not in " ".join(map(str, record.args))


def test_filter_never_raises_on_unexpected_msg_type():
    flt = RedactingFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="x.py",
        lineno=1,
        msg={"k": "password=secret"},  # type: ignore[arg-type]
        args=(),
        exc_info=None,
    )
    # Even with a non-string msg, filter() must return True and not crash.
    assert flt.filter(record) is True
