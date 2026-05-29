"""In-memory job store (demo-scoped).

A real deployment would back this with Cosmos DB / table storage behind the same interface;
the routes depend on the instance via ``app.state``, so swapping it is a one-line change.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class JobRecord:
    job_id: str
    invoice_ref: str
    status: str  # completed | failed
    detail: dict[str, Any]  # JSON-safe job detail (see service.serialize_run)
    events: list[dict[str, Any]]
    human_decision: dict[str, Any] | None = None


@dataclass
class JobStore:
    _jobs: dict[str, JobRecord] = field(default_factory=dict)

    def put(self, record: JobRecord) -> None:
        self._jobs[record.job_id] = record

    def get(self, job_id: str) -> JobRecord | None:
        return self._jobs.get(job_id)
