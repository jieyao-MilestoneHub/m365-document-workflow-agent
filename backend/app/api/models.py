"""Request/response models for the API.

Inputs are strictly validated; the rich job detail is returned as a JSON-safe dict assembled
in :mod:`app.api.service` (FastAPI encodes nested Decimals).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CreateJobRequest(BaseModel):
    #: Used to build a filesystem path (``<data>/invoices/<ref>.json``), so it is constrained
    #: to a safe filename charset — no path separators or other traversal characters.
    invoice_ref: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9._-]+$",
        description="e.g. INV-1042 (letters, digits, dot, dash, underscore only)",
    )


class DecisionRequest(BaseModel):
    action: Literal["approve", "reject"]
    reviewer: str = Field(min_length=1)
    note: str | None = None


class ScenarioInfo(BaseModel):
    id: str
    vendor: str
    total: str
    currency: str
