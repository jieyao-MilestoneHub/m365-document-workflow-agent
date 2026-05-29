"use client";

import { useReasoningStream } from "@/hooks/useReasoningStream";
import { formatTimestamp } from "@/lib/format";

const STATUS_LABEL: Record<string, string> = {
  streaming: "streaming…",
  completed: "complete",
  error: "stream error",
};

/**
 * Live SSE reasoning timeline. Each trace event (kind/role/detail) is rendered as plain text;
 * the stream is owned by the api boundary via the useReasoningStream hook.
 */
export function AgentReasoningTrace({ jobId }: { jobId: string }) {
  const { events, status, error } = useReasoningStream(jobId);

  return (
    <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-800">Agent reasoning trace</h3>
        <span
          className={`text-xs ${status === "error" ? "text-red-600" : "text-slate-500"}`}
          aria-live="polite"
        >
          {STATUS_LABEL[status]}
        </span>
      </div>

      {error && <p className="text-xs text-red-600">{error}</p>}

      {events.length === 0 && status === "streaming" ? (
        <p className="text-sm text-slate-500">Waiting for the agent to start reasoning…</p>
      ) : (
        <ol className="space-y-3">
          {events.map((event) => (
            <li key={event.seq} className="flex gap-3">
              <div className="flex flex-col items-center">
                <span className="mt-1 h-2 w-2 rounded-full bg-blue-500" />
                <span className="w-px flex-1 bg-slate-200" />
              </div>
              <div className="pb-1">
                <p className="text-sm text-slate-800">
                  <span className="font-medium">{event.role}</span>
                  <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs text-slate-500">
                    {event.kind}
                  </span>
                </p>
                <p className="text-sm text-slate-600">{event.detail}</p>
                <p className="text-xs text-slate-400">{formatTimestamp(event.ts)}</p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
