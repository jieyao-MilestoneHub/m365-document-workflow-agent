"""API tests via Starlette TestClient (offline, against the sample fixtures)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api import service
from app.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_scenarios_lists_invoices(client):
    data = client.get("/api/scenarios").json()
    ids = {s["id"] for s in data}
    # the inbox must surface the core cases and the freight/UOM stretch scenarios
    assert {"INV-1042", "INV-1043", "INV-1057", "INV-1059", "INV-1060"} <= ids


def test_create_job_holds_variance(client):
    detail = client.post("/api/jobs", json={"invoice_ref": "INV-1042"}).json()
    assert detail["decision"] == "hold"
    assert "VARIANCE_OUTSIDE_TOLERANCE" in detail["outcome"]["blocking_reasons"]


def test_create_job_returns_citations(client):
    detail = client.post("/api/jobs", json={"invoice_ref": "INV-1043"}).json()
    citations = detail["match"]["citations"]
    # exactly the PO and GRN that were looked up, in order
    assert [c["document_id"] for c in citations] == ["PO-5000", "GRN-7000"]


def test_get_job_roundtrip(client):
    created = client.post("/api/jobs", json={"invoice_ref": "INV-1043"}).json()
    fetched = client.get(f"/api/jobs/{created['job_id']}").json()
    assert fetched["job_id"] == created["job_id"]
    assert fetched["invoice_ref"] == created["invoice_ref"]
    assert fetched["status"] == "completed"
    assert fetched["decision"] == "pass"
    assert fetched["outcome"]["decision"] == "pass"


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
    decision = updated["human_decision"]
    assert decision["action"] == "approve"
    assert decision["reviewer"] == "ap.manager@globex.test"
    assert decision["note"] == "ok"
    assert decision["ts"]  # apply_decision stamps a UTC timestamp


def test_handoff_history_present(client):
    detail = client.post("/api/jobs", json={"invoice_ref": "INV-1043"}).json()
    # clean path: extractor → matcher → promotion_auditor → variance → posting → reviewer → finalize
    assert len(detail["handoff_history"]) == 7


def test_stream_emits_trace_then_completed(client):
    job = client.post("/api/jobs", json={"invoice_ref": "INV-1042"}).json()
    body = client.get(f"/api/jobs/{job['job_id']}/stream").text
    # one trace per emitted event (deterministic): 6 delegate_result + 1 peer_review + 1 finalize
    assert body.count("event: trace") == 8
    assert "event: completed" in body
    assert "hold" in body


def test_stream_unknown_job_404(client):
    assert client.get("/api/jobs/deadbeef/stream").status_code == 404


# --- security: invoice_ref must not allow path traversal -----------------------

@pytest.mark.parametrize(
    "evil",
    [
        "../../../../etc/passwd",
        "..\\..\\..\\windows\\win.ini",
        "foo/bar",
        "/etc/hosts",
        "a/../b",
    ],
)
def test_invoice_ref_with_separators_rejected(client, evil):
    # path separators are outside the allowed charset → rejected by validation (422),
    # before any filesystem access happens
    assert client.post("/api/jobs", json={"invoice_ref": evil}).status_code == 422


def test_run_job_containment_guard_blocks_escape(sample_data_dir):
    # defense in depth: even bypassing the request model, the service refuses a ref that
    # resolves outside the invoices directory (raises 404-equivalent, never reads the file)
    with pytest.raises(FileNotFoundError):
        service.run_job("../../../../etc/passwd", base_dir=sample_data_dir)


def test_valid_invoice_ref_still_accepted(client):
    # the hardening must not break a legitimate id
    assert client.post("/api/jobs", json={"invoice_ref": "INV-1043"}).status_code == 200
