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

/**
 * Subscribes to a job's reasoning-trace SSE stream and accumulates trace events until the
 * terminal `completed` event. Delegates all EventSource handling to the api boundary.
 */
export function useReasoningStream(jobId: string | undefined): ReasoningStream {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [completed, setCompleted] = useState<StreamCompleted | null>(null);
  const [status, setStatus] = useState<StreamStatus>("streaming");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;
    setEvents([]);
    setCompleted(null);
    setStatus("streaming");
    setError(null);

    const dispose = api.openStream(jobId, {
      onTrace: (event) =>
        setEvents((prev) =>
          prev.some((e) => e.seq === event.seq)
            ? prev
            : [...prev, event].sort((a, b) => a.seq - b.seq),
        ),
      onCompleted: (event) => {
        setCompleted(event);
        setStatus("completed");
      },
      onError: (err) => {
        setError(err.message);
        setStatus("error");
      },
    });
    return dispose;
  }, [jobId]);

  return { events, completed, status, error };
}
