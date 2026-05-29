"""Purchase Order (PO) and Goods Receipt Note (GRN) reference documents.

Retrieved from Foundry IQ by the po_grn_matcher specialist (with citations). The matcher
compares the invoice against these; it must never invent a PO/GRN line.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class POLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    sku: str | None = None
    description: str
    quantity: Decimal
    unit_price: Decimal


class PurchaseOrder(BaseModel):
    model_config = ConfigDict(frozen=True)

    po_number: str
    vendor_name: str
    currency: str = Field(min_length=3, max_length=3)
    lines: list[POLine] = Field(default_factory=list)


class GRNLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    sku: str | None = None
    description: str
    received_quantity: Decimal


class GoodsReceiptNote(BaseModel):
    model_config = ConfigDict(frozen=True)

    grn_number: str
    receipt_date: date | None = None
    lines: list[GRNLine] = Field(default_factory=list)
