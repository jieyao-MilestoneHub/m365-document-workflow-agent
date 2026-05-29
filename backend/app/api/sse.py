"""Server-Sent Events stream of a job's reasoning trace.

Emits one ``trace`` event per supervisor step, then a terminal ``completed`` event with the
verdict. The offline run is instant, so this replays the stored events; the wire contract is
identical to a live stream, so the frontend is unchanged if execution later moves behind
Azure latency (the events would then be pushed as they happen).
"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator

from sse_starlette.sse import EventSourceResponse

from .store import JobRecord


async def _event_stream(record: JobRecord) -> AsyncIterator[dict]:
    for event in record.events:
        yield {"event": "trace", "data": json.dumps(event)}
    outcome = record.detail["outcome"]
    yield {
        "event": "completed",
        "data": json.dumps({
            "job_id": record.job_id,
            "decision": record.detail["decision"],
            "summary": outcome["summary"],
            "blocking_reasons": outcome["blocking_reasons"],
        }),
    }


def stream_job(record: JobRecord) -> EventSourceResponse:
    return EventSourceResponse(_event_stream(record))
