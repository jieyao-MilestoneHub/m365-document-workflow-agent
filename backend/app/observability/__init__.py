"""Observability primitives — SOLID-isolated log, trace, metrics, and error handlers.

The deterministic core (``app/schemas``, ``app/orchestrator/validators.py``,
``app/orchestrator/guardrails.py``) MUST remain importable and runnable without any of the
optional packages listed in the ``observability`` extra. Every module here is written so
that the absence of ``opentelemetry``, ``redactkit``, or ``agent_framework`` degrades to a
no-op rather than raising at import time.
"""
from __future__ import annotations

from . import metrics
from .config import configure_observability, is_enabled
from .ports import LoggerPort, MetricsPort, TracerPort

__all__ = [
    "LoggerPort",
    "MetricsPort",
    "TracerPort",
    "configure_observability",
    "is_enabled",
    "metrics",
]
