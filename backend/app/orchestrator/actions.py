"""Supervisor actions — the closed set of moves the supervisor brain can make each turn.

Mirrors convilyn's four structured tool-calls: delegate / peer-review / escalate / finalize.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Delegate:
    """Hand the run to a specialist."""

    role: str
    reason: str = ""


@dataclass(frozen=True)
class PeerReview:
    """Ask one specialist to verify another's claim (minimal-context review)."""

    reviewer: str
    subject_role: str
    claim: str
    question: str


@dataclass(frozen=True)
class Escalate:
    """Abandon automation and route to a human."""

    reason_code: str
    summary: str


@dataclass(frozen=True)
class Finalize:
    """Terminate the run; the outcome is computed by the authoritative decision matrix."""


SupervisorAction = Union[Delegate, PeerReview, Escalate, Finalize]
