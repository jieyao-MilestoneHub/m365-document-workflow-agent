"""Application service: run a job, serialize it JSON-safe, list scenarios, record decisions."""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.orchestrator.roles import (
    EXCEPTION_REVIEWER,
    INVOICE_EXTRACTOR,
    PO_GRN_MATCHER,
    POSTING_PREPARER,
    VARIANCE_ASSESSOR,
)
from app.orchestrator.supervisor import SupervisorRun
from app.runner import DEFAULT_DATA_DIR, run

from .store import JobRecord, JobStore


def _dump(payload) -> dict | None:
    return payload.model_dump(mode="json") if payload is not None else None


def serialize_run(run_result: SupervisorRun, *, job_id: str, invoice_ref: str) -> JobRecord:
    """Turn a SupervisorRun into a JSON-safe JobRecord."""
    env = run_result.envelope
    events = [asdict(e) for e in run_result.events]
    detail: dict[str, Any] = {
        "job_id": job_id,
        "invoice_ref": invoice_ref,
        "status": "completed",
        "decision": run_result.outcome.decision.value,
        "outcome": run_result.outcome.model_dump(mode="json"),
        "invoice": _dump(env.payload_for(INVOICE_EXTRACTOR)),
        "match": _dump(env.payload_for(PO_GRN_MATCHER)),
        "variance": _dump(env.payload_for(VARIANCE_ASSESSOR)),
        "posting": _dump(env.payload_for(POSTING_PREPARER)),
        "review": _dump(env.payload_for(EXCEPTION_REVIEWER)),
        "handoff_history": [asdict(h) for h in env.handoff_history],
        "events": events,
        "human_decision": None,
    }
    return JobRecord(
        job_id=job_id, invoice_ref=invoice_ref, status="completed",
        detail=detail, events=events,
    )


def run_job(invoice_ref: str, *, base_dir: str | Path = DEFAULT_DATA_DIR) -> JobRecord:
    # 404 for a non-existent invoice; in-band extraction failures still escalate (not 404).
    if not (Path(base_dir) / "invoices" / f"{invoice_ref}.json").exists():
        raise FileNotFoundError(f"no invoice {invoice_ref}")
    job_id = uuid.uuid4().hex[:12]
    return serialize_run(run(invoice_ref, base_dir=base_dir), job_id=job_id, invoice_ref=invoice_ref)


def list_scenarios(*, base_dir: str | Path = DEFAULT_DATA_DIR) -> list[dict]:
    """List available sample invoices for the inbox (no expected-verdict leakage)."""
    inv_dir = Path(base_dir) / "invoices"
    out: list[dict] = []
    for path in sorted(inv_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        out.append({
            "id": data.get("invoice_number", path.stem),
            "vendor": data.get("vendor_name", ""),
            "total": str(data.get("total", "")),
            "currency": data.get("currency", ""),
        })
    return out


def apply_decision(record: JobRecord, *, action: str, reviewer: str, note: str | None) -> JobRecord:
    """Record a human verdict on a held/escalated job (approver inbox + audit)."""
    decision = {
        "action": action, "reviewer": reviewer, "note": note,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    record.human_decision = decision
    record.detail["human_decision"] = decision
    return record


def store_job(store: JobStore, record: JobRecord) -> JobRecord:
    store.put(record)
    return record
