"""HTTP routes for the three-way-match agent."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request

from . import service
from .models import CreateJobRequest, DecisionRequest
from .sse import stream_job
from .store import JobStore

router = APIRouter(prefix="/api")


def get_store(request: Request) -> JobStore:
    return request.app.state.store


def get_base_dir(request: Request) -> Path:
    return request.app.state.base_dir


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/scenarios")
def scenarios(base_dir: Path = Depends(get_base_dir)) -> list[dict]:
    return service.list_scenarios(base_dir=base_dir)


@router.post("/jobs")
def create_job(
    body: CreateJobRequest,
    store: JobStore = Depends(get_store),
    base_dir: Path = Depends(get_base_dir),
) -> dict:
    try:
        record = service.run_job(body.invoice_ref, base_dir=base_dir)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    service.store_job(store, record)
    return record.detail


@router.get("/jobs/{job_id}")
def get_job(job_id: str, store: JobStore = Depends(get_store)) -> dict:
    record = store.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"unknown job {job_id}")
    return record.detail


@router.get("/jobs/{job_id}/stream")
def stream(job_id: str, store: JobStore = Depends(get_store)):
    record = store.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"unknown job {job_id}")
    return stream_job(record)


@router.post("/jobs/{job_id}/decision")
def decide(
    job_id: str, body: DecisionRequest, store: JobStore = Depends(get_store)
) -> dict:
    record = store.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"unknown job {job_id}")
    service.apply_decision(record, action=body.action, reviewer=body.reviewer, note=body.note)
    return record.detail
