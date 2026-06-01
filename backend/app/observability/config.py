"""Wire OpenTelemetry providers and log handlers from environment variables.

This is the *only* file that knows how to bootstrap the Microsoft Agent Framework's
official OTel hookup. When ``ENABLE_INSTRUMENTATION`` is unset (or not truthy), this
module is a no-op — preserving the project's hard constraint that the deterministic core
runs without any Azure / M365 credentials.

When enabled:

* Delegates to ``agent_framework.observability.configure_otel_providers`` if available
  (Microsoft official entry point — emits GenAI semantic-convention spans suitable for
  the Application Insights "Agents (Preview)" view).
* Attaches a :class:`~app.observability.redaction.RedactingFilter` to the root logger,
  so secrets and PII never reach Application Insights via log messages.

Both side effects are best-effort: a missing optional dependency or a configuration error
must NOT crash the application at startup.
"""
from __future__ import annotations

import logging
import os

#: Environment variable that gates *all* observability side effects.
INSTRUMENTATION_ENV = "ENABLE_INSTRUMENTATION"
#: Service-name attribute attached to every OTel signal.
SERVICE_NAME_ENV = "OTEL_SERVICE_NAME"
#: Default service name when none is supplied.
DEFAULT_SERVICE_NAME = "ap-three-way-match"


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def is_enabled() -> bool:
    """True iff ``ENABLE_INSTRUMENTATION`` is set to a truthy value."""
    return _truthy(os.getenv(INSTRUMENTATION_ENV))


def configure_observability() -> bool:
    """Configure OpenTelemetry providers and the redaction-aware log filter.

    Returns ``True`` if instrumentation was actually requested (env enabled), regardless of
    whether optional packages were present — the function never raises and always degrades
    to whatever subset of telemetry is locally available.
    """
    if not is_enabled():
        return False

    os.environ.setdefault(SERVICE_NAME_ENV, DEFAULT_SERVICE_NAME)
    _try_configure_agent_framework()
    _attach_redaction_filter()
    return True


def _try_configure_agent_framework() -> None:
    """Best-effort call into the Microsoft Agent Framework's official OTel hookup."""
    try:
        from agent_framework.observability import configure_otel_providers
    except ImportError:
        return
    try:
        configure_otel_providers()
    except Exception:  # pragma: no cover - defensive: never crash startup on telemetry
        logging.getLogger(__name__).exception("failed to configure OTel providers")


def _attach_redaction_filter() -> None:
    """Insert :class:`RedactingFilter` on every root-logger handler (idempotent).

    PR1 leaves this as a no-op when the :mod:`app.observability.redaction` module is
    absent; PR2 introduces the filter and this function picks it up automatically.
    """
    try:
        from .redaction import RedactingFilter
    except ImportError:
        return

    root = logging.getLogger()
    for handler in root.handlers:
        if not any(isinstance(f, RedactingFilter) for f in handler.filters):
            handler.addFilter(RedactingFilter())
