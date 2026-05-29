"""Request/response models for the API.

Inputs are strictly validated; the rich job detail is returned as a JSON-safe dict assembled
in :mod:`app.api.service` (FastAPI encodes nested Decimals).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CreateJobRequest(BaseModel):
    invoice_ref: str = Field(min_length=1, description="e.g. INV-1042")


class DecisionRequest(BaseModel):
    action: Literal["approve", "reject"]
    reviewer: str = Field(min_length=1)
    note: str | None = None


class ScenarioInfo(BaseModel):
    id: str
    vendor: str
    total: str
    currency: str
