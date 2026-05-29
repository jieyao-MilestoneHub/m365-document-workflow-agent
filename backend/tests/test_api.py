"""API tests via Starlette TestClient (offline, against the sample fixtures)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_scenarios_lists_invoices(client):
    data = client.get("/api/scenarios").json()
    ids = {s["id"] for s in data}
    assert {"INV-1042", "INV-1043", "INV-1057"} <= ids


def test_create_job_holds_variance(client):
    detail = client.post("/api/jobs", json={"invoice_ref": "INV-1042"}).json()
    assert detail["decision"] == "hold"
    assert "VARIANCE_OUTSIDE_TOLERANCE" in detail["outcome"]["blocking_reasons"]


def test_create_job_returns_citations(client):
    detail = client.post("/api/jobs", json={"invoice_ref": "INV-1043"}).json()
    assert detail["match"]["citations"]


def test_get_job_roundtrip(client):
    created = client.post("/api/jobs", json={"invoice_ref": "INV-1043"}).json()
    fetched = client.get(f"/api/jobs/{created['job_id']}").json()
    assert fetched["job_id"] == created["job_id"]
    assert fetched["decision"] == "pass"


def test_unknown_invoice_404(client):
    assert client.post("/api/jobs", json={"invoice_ref": "NOPE"}).status_code == 404


def test_unknown_job_404(client):
    assert client.get("/api/jobs/deadbeef").status_code == 404


def test_decision_recorded(client):
    job = client.post("/api/jobs", json={"invoice_ref": "INV-1042"}).json()
    updated = client.post(
        f"/api/jobs/{job['job_id']}/decision",
        json={"action": "approve", "reviewer": "ap.manager@globex.test", "note": "ok"},
    ).json()
    assert updated["human_decision"]["action"] == "approve"
    assert updated["human_decision"]["reviewer"] == "ap.manager@globex.test"


def test_handoff_history_present(client):
    detail = client.post("/api/jobs", json={"invoice_ref": "INV-1043"}).json()
    assert len(detail["handoff_history"]) >= 5
