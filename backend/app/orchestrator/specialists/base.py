"""The Specialist protocol.

A specialist reads the prior results it needs from the envelope, does its one job, and
returns a :class:`SpecialistResult`. It must NOT mutate the envelope — the supervisor loop
applies the result functionally.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..envelope import MultiAgentEnvelope, SpecialistResult


@runtime_checkable
class Specialist(Protocol):
    role: str

    def run(self, envelope: MultiAgentEnvelope) -> SpecialistResult: ...
