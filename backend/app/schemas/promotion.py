"""Trade-promotion agreement schema.

A promotion is the commercial condition that lives *outside* the PO/GRN/invoice triad: a
per-unit allowance the supplier owes the retailer for a SKU over a date window. The
``promotion_auditor`` reconciles each invoice against the promotions in effect for its vendor,
so an invoice that matches its PO and GRN exactly can still be held for a missing allowance.

In production these are retrieved (with citations) from Foundry IQ via the ``KnowledgePort``;
offline they come from ``sample-data/promotions.json``.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class Promotion(BaseModel):
    """A trade-promotion allowance agreement. Immutable reference data."""

    model_config = ConfigDict(frozen=True)

    promo_id: str
    description: str = ""
    vendor_name: str
    #: SKU the allowance applies to (None = all SKUs from the vendor)
    sku: str | None = None
    allowance_per_unit: Decimal = Field(ge=0, description="allowance owed per unit (currency)")
    unit_of_measure: str | None = None
    effective_from: date
    effective_to: date
    #: where a missing-allowance deduction should be routed
    route_to: str = "category_manager"

    def applies_on(self, when: date) -> bool:
        """True when ``when`` falls within the effective window (inclusive)."""
        return self.effective_from <= when <= self.effective_to
