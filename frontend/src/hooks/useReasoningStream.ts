"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { StreamCompleted, TraceEvent } from "@/lib/types";

export type StreamStatus = "streaming" | "completed" | "error";

export interface ReasoningStream {
  events: TraceEvent[];
  completed: StreamCompleted | null;
  status: StreamStatus;
  error: string | null;
}

interface InternalState extends ReasoningStream {
  jobId: string | undefined;
}

const fresh = (jobId: string | undefined): InternalState => ({
  jobId,
  events: [],
  completed: null,
  status: "streaming",
  error: null,
});

/**
 * Subscribes to a job's reasoning-trace SSE stream and accumulates trace events until the
 * terminal `completed` event. Delegates all EventSource handling to the api boundary.
 *
 * State is reset during render when `jobId` changes (the React-recommended pattern) rather
 * than in the effect, so switching jobs never shows the previous job's events.
 */
export function useReasoningStream(jobId: string | undefined): ReasoningStream {
  const [state, setState] = useState<InternalState>(() => fresh(jobId));

  if (state.jobId !== jobId) {
    setState(fresh(jobId));
  }

  useEffect(() => {
    if (!jobId) return;
    // Guard updates to the job this effect was opened for (ignore late events after a switch).
    const apply = (fn: (s: InternalState) => InternalState) =>
      setState((s) => (s.jobId === jobId ? fn(s) : s));

    const dispose = api.openStream(jobId, {
      onTrace: (event) =>
        apply((s) => ({
          ...s,
          events: s.events.some((e) => e.seq === event.seq)
            ? s.events
            : [...s.events, event].sort((a, b) => a.seq - b.seq),
        })),
      onCompleted: (event) => apply((s) => ({ ...s, completed: event, status: "completed" })),
      onError: (err) => apply((s) => ({ ...s, error: err.message, status: "error" })),
    });
    return dispose;
  }, [jobId]);

  return state;
}
