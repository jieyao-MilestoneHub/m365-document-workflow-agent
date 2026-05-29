from decimal import Decimal

from app.schemas.money import money_close, to_money


def test_to_money_quantizes_to_two_places():
    assert to_money("10.005") == Decimal("10.01")


def test_to_money_accepts_float_without_binary_drift():
    assert to_money(0.1 + 0.2) == Decimal("0.30")


def test_money_close_true_within_one_cent():
    assert money_close(Decimal("10.00"), Decimal("10.01")) is True


def test_money_close_false_beyond_one_cent():
    assert money_close(Decimal("10.00"), Decimal("10.02")) is False
