"""FastAPI application factory.

    uvicorn "app.api.app:create_app" --factory --reload
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.runner import DEFAULT_DATA_DIR

from .routes import router
from .store import JobStore

# Next.js dev origin by default; override with API_CORS_ORIGINS="https://a,https://b".
_DEFAULT_ORIGINS = "http://localhost:3000"


def create_app(base_dir: str | Path = DEFAULT_DATA_DIR) -> FastAPI:
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
    app.include_router(router)
    return app
