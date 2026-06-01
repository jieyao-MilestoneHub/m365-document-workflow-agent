"""Domain → HTTP problem+json translation tests."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.observability.exceptions import (
    NotFoundError,
    UpstreamError,
    register_exception_handlers,
)


def test_unknown_invoice_returns_problem_json():
    client = TestClient(create_app())
    r = client.post("/api/jobs", json={"invoice_ref": "NOPE"})
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert body["type"] == "urn:apthreeway:not_found"
    assert body["status"] == 404
    assert body["instance"] == "/api/jobs"
    assert body["request_id"]  # populated by CorrelationMiddleware


def test_unknown_job_returns_problem_json():
    client = TestClient(create_app())
    r = client.get("/api/jobs/deadbeef")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert body["status"] == 404
    assert "deadbeef" in body["detail"]


def test_validation_error_returns_problem_json():
    client = TestClient(create_app())
    # path-traversal candidate is rejected by Pydantic field validation (422).
    r = client.post("/api/jobs", json={"invoice_ref": "../etc/passwd"})
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert body["status"] == 422
    assert body["request_id"]


def test_unhandled_exception_returns_500_without_leaking_detail():
    # Build a minimal app that raises a non-AppError to exercise the catch-all.
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    def boom():
        raise RuntimeError("sensitive vendor name and tax_id=VAT123456789")

    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/boom")
    assert r.status_code == 500
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert body["detail"] == "An internal error occurred."
    # Secret-leak regression guard: the original message must not appear anywhere in the body.
    assert "VAT123456789" not in r.text


def test_app_error_subclasses_translate_to_correct_status():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/missing")
    def missing():
        raise NotFoundError("widget gone")

    @app.get("/upstream-down")
    def upstream():
        raise UpstreamError("foundry iq timed out")

    client = TestClient(app)
    r1 = client.get("/missing")
    assert r1.status_code == 404
    assert r1.json()["type"] == "urn:apthreeway:not_found"
    assert r1.json()["detail"] == "widget gone"

    r2 = client.get("/upstream-down")
    assert r2.status_code == 502
    assert r2.json()["type"] == "urn:apthreeway:upstream_error"
