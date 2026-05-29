"""Policy reference data: tolerance, GL account map, vendor configuration.

In production these are loaded from a config store / Foundry IQ knowledge base. They are
frozen for the duration of a run — a specialist must NOT widen tolerance to force a match.
"""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TolerancePolicy(BaseModel):
    """Per-line matching tolerance. Immutable per run."""

    model_config = ConfigDict(frozen=True)

    version: str = "2026.04.1"
    quantity_absolute: Decimal = Field(default=Decimal("0.5"), description="units")
    price_absolute: Decimal = Field(default=Decimal("0.5"), description="currency units")
    price_percent: Decimal = Field(default=Decimal("0.02"), description="fraction of PO unit price")

    def price_limit(self, po_unit_price: Decimal) -> Decimal:
        """Allowed absolute price delta for a line: max(absolute, percent × PO unit price)."""
        return max(self.price_absolute, (po_unit_price * self.price_percent).copy_abs())


class VarianceThresholds(BaseModel):
    """Financial-impact thresholds that grade variance severity."""

    model_config = ConfigDict(frozen=True)

    version: str = "2026.04.1"
    medium_threshold: Decimal = Field(default=Decimal("50.00"))
    high_threshold: Decimal = Field(default=Decimal("500.00"))


class GLMap(BaseModel):
    """Chart-of-accounts routing for posting."""

    model_config = ConfigDict(frozen=True)

    version: str = "ap.gl.v1"
    ap_liability: str = "2100"
    expense_fallback: str = "5000"
    tax: str = "1360"
    #: optional SKU/category → expense account overrides
    overrides: dict[str, str] = Field(default_factory=dict)

    def expense_account(self, key: str | None) -> str:
        """Resolve a line's expense account, falling back to the default expense account."""
        if key and key in self.overrides:
            return self.overrides[key]
        return self.expense_fallback


class VendorConfig(BaseModel):
    """Vendor governance lists."""

    model_config = ConfigDict(frozen=True)

    auto_post_vendors: list[str] = Field(default_factory=list)
    hold_on_vendors: list[str] = Field(default_factory=list)
    gray_zone_vendors: list[str] = Field(default_factory=list)


class PolicyBundle(BaseModel):
    """All frozen reference data for one run, retrieved from Foundry IQ."""

    model_config = ConfigDict(frozen=True)

    tolerance: TolerancePolicy = Field(default_factory=TolerancePolicy)
    thresholds: VarianceThresholds = Field(default_factory=VarianceThresholds)
    gl_map: GLMap = Field(default_factory=GLMap)
    vendors: VendorConfig = Field(default_factory=VendorConfig)
    valid_gl_accounts: frozenset[str] = Field(default_factory=frozenset)
    closed_periods: frozenset[str] = Field(default_factory=frozenset, description="YYYY-MM strings")
