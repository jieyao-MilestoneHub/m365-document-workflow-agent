"""FastAPI application factory.

    uvicorn "app.api.app:create_app" --factory --reload
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.observability import (
    CorrelationMiddleware,
    configure_observability,
    register_exception_handlers,
)
from app.runner import DEFAULT_DATA_DIR

from .routes import router
from .store import JobStore

# Next.js dev origin by default; override with API_CORS_ORIGINS="https://a,https://b".
_DEFAULT_ORIGINS = "http://localhost:3000"


def create_app(base_dir: str | Path = DEFAULT_DATA_DIR) -> FastAPI:
    # Best-effort, env-gated. No-op when ENABLE_INSTRUMENTATION is unset, so offline
    # tests and the deterministic core stay cloud-credential-free.
    configure_observability()

    app = FastAPI(title="AP Three-Way Match Agent", version="0.1.0")
    app.state.store = JobStore()
    app.state.base_dir = Path(base_dir)

    origins = os.getenv("API_CORS_ORIGINS", _DEFAULT_ORIGINS).split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins if o.strip()],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Added after CORS so it ends up outermost in the middleware stack: every request,
    # including CORS-rejected preflights, gets an x-request-id back.
    app.add_middleware(CorrelationMiddleware)

    register_exception_handlers(app)
    app.include_router(router)
    return app
