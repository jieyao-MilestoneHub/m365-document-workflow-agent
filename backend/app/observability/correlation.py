"""Request correlation: ContextVars + ASGI middleware.

Generates or propagates a ``request_id`` and the W3C ``traceparent`` header on every
inbound request. Stored in :mod:`contextvars` so any code path in the request lifecycle —
handlers, supervisor, specialists, log filters — can read them without explicit plumbing.

Why ContextVars and not request.state: ContextVars survive across ``asyncio`` task
boundaries and are accessible from synchronous code paths (e.g. the supervisor loop and
:class:`~app.observability.redaction.RedactingFilter`) without a request object in scope.
"""
from __future__ import annotations

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

REQUEST_ID_HEADER = "x-request-id"
TRACEPARENT_HEADER = "traceparent"

request_id: ContextVar[str] = ContextVar("request_id", default="")
traceparent: ContextVar[str] = ContextVar("traceparent", default="")


def new_request_id() -> str:
    """A short, opaque request identifier (uuid4 hex, 32 chars)."""
    return uuid.uuid4().hex


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Read/generate ``x-request-id`` and ``traceparent``, echo on the response."""

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get(REQUEST_ID_HEADER) or new_request_id()
        tp = request.headers.get(TRACEPARENT_HEADER, "")
        rid_token = request_id.set(rid)
        tp_token = traceparent.set(tp)
        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = rid
            return response
        finally:
            request_id.reset(rid_token)
            traceparent.reset(tp_token)
