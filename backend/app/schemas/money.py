"""Decimal money helpers.

Money is represented as :class:`decimal.Decimal` everywhere — never float — so that
arithmetic invariants (line totals, posting balance) hold to the cent.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")


def to_money(value: str | int | float | Decimal) -> Decimal:
    """Quantize an arbitrary numeric value to 2 decimal places (banker-free, half-up)."""
    return Decimal(str(value)).quantize(CENTS, rounding=ROUND_HALF_UP)


def money_close(a: Decimal, b: Decimal, tol: Decimal = CENTS) -> bool:
    """True when two monetary amounts are within ``tol`` (default one cent)."""
    return abs(Decimal(a) - Decimal(b)) <= tol
