"""Correlation ID middleware tests."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.app import create_app
from app.observability.correlation import REQUEST_ID_HEADER


def test_request_id_is_set_on_every_response():
    client = TestClient(create_app())
    r = client.get("/api/health")
    assert r.status_code == 200
    rid = r.headers.get(REQUEST_ID_HEADER)
    assert rid is not None
    assert len(rid) >= 16  # uuid4 hex is 32 chars


def test_inbound_request_id_is_preserved_in_response():
    client = TestClient(create_app())
    incoming = "trace-abc-1234567890ef"
    r = client.get("/api/health", headers={REQUEST_ID_HEADER: incoming})
    assert r.headers[REQUEST_ID_HEADER] == incoming


def test_request_id_changes_between_requests_when_not_supplied():
    client = TestClient(create_app())
    r1 = client.get("/api/health").headers[REQUEST_ID_HEADER]
    r2 = client.get("/api/health").headers[REQUEST_ID_HEADER]
    assert r1 and r2 and r1 != r2


def test_request_id_present_on_error_response():
    client = TestClient(create_app())
    r = client.get("/api/jobs/deadbeef")
    assert r.status_code == 404
    assert r.headers.get(REQUEST_ID_HEADER)
