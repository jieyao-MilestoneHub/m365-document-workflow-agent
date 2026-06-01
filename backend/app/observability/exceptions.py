"""Domain → HTTP error translation. Pure mapper + thin FastAPI handlers.

The mapping is a stateless function (:func:`translate`) — easy to unit-test, no FastAPI
dependency at the call site. The three registered handlers are thin shells that defer to
``translate``. This preserves SRP: domain code raises domain errors, HTTP-shape concerns
live in one place.

All responses use ``application/problem+json`` (RFC 7807). The body carries the
``request_id`` and ``traceparent`` from :mod:`app.observability.correlation`, so a client
error can be cross-referenced against the corresponding Application Insights trace.

The 500 catch-all NEVER echoes the exception message back to the client — it is logged
(through the :class:`~app.observability.redaction.RedactingFilter`) and the client gets a
generic detail. This closes a real gap: prior to this module, an unhandled exception
returned Starlette's default HTML page, potentially leaking internals to the M365 client.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request

from .correlation import request_id, traceparent

_logger = logging.getLogger("app.observability")

PROBLEM_JSON = "application/problem+json"
_URN_PREFIX = "urn:apthreeway"


class AppError(Exception):
    """Base domain error — subclasses define the HTTP shape via class attrs (LSP)."""

    status_code: int = 500
    code: str = "internal_error"
    title: str = "Internal Server Error"

    def __init__(self, detail: str = "") -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(AppError):
    status_code, code, title = 404, "not_found", "Not Found"


class ValidationError(AppError):
    status_code, code, title = 422, "validation_error", "Unprocessable Entity"


class UpstreamError(AppError):
    status_code, code, title = 502, "upstream_error", "Bad Gateway"


def _problem_body(*, status: int, code: str, title: str, detail: str, path: str) -> dict[str, Any]:
    return {
        "type": f"{_URN_PREFIX}:{code}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": path,
        "request_id": request_id.get(""),
        "traceparent": traceparent.get(""),
    }


def _response(*, status: int, code: str, title: str, detail: str, path: str) -> JSONResponse:
    body = _problem_body(status=status, code=code, title=title, detail=detail, path=path)
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON)


def translate(exc: Exception, request: Request) -> JSONResponse:
    """Pure mapper — domain or unknown exception → problem+json response."""
    path = str(request.url.path)
    if isinstance(exc, AppError):
        return _response(
            status=exc.status_code, code=exc.code, title=exc.title, detail=exc.detail, path=path
        )
    if isinstance(exc, RequestValidationError):
        return _response(
            status=422,
            code="validation_error",
            title="Unprocessable Entity",
            detail=str(exc.errors()),
            path=path,
        )
    # Unknown exception — log full context (redacted) and surface a generic detail.
    _logger.exception(
        "unhandled exception path=%s request_id=%s", path, request_id.get("")
    )
    return _response(
        status=500,
        code="internal_error",
        title="Internal Server Error",
        detail="An internal error occurred.",
        path=path,
    )


# --- FastAPI handlers (thin shells over translate) -----------------------------------------


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return translate(exc, request)


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return translate(exc, request)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return translate(exc, request)


def register_exception_handlers(app: FastAPI) -> None:
    """Register the three handlers on the FastAPI app (idempotent for a given app)."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
