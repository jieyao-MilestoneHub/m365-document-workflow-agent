"use client";

import { SparkleIcon } from "@/components/ui/icons";
import { useReasoningStream } from "@/hooks/useReasoningStream";
import { formatTimestamp } from "@/lib/format";
import { Section } from "@/components/ui/section";

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

  const statusTone =
    status === "error" ? "text-danger" : status === "completed" ? "text-success" : "text-brand";

  return (
    <Section
      title="Agent reasoning trace"
      icon={SparkleIcon}
      aside={
        <span className={`flex items-center gap-1.5 text-xs font-semibold ${statusTone}`} aria-live="polite">
          {status === "streaming" && (
            <span className="h-1.5 w-1.5 rounded-full bg-brand pulse-dot" aria-hidden="true" />
          )}
          {STATUS_LABEL[status]}
        </span>
      }
    >
      {error && <p className="mb-2 text-xs text-danger">{error}</p>}

      {events.length === 0 && status === "streaming" ? (
        <p className="text-sm text-muted">Waiting for the agent to start reasoning…</p>
      ) : (
        <ol className="space-y-0">
          {events.map((event, i) => {
            const last = i === events.length - 1;
            return (
              <li key={event.seq} className="flex gap-3">
                <div className="flex flex-col items-center">
                  <span className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full bg-brand ring-4 ring-brand-tint" />
                  {!last && <span className="w-px flex-1 bg-stroke" />}
                </div>
                <div className={last ? "pb-0.5" : "pb-5"}>
                  <p className="flex flex-wrap items-center gap-2 text-sm">
                    <span className="font-semibold text-ink">{event.role}</span>
                    <span className="rounded bg-surface-muted px-1.5 py-0.5 font-mono text-[11px] text-muted ring-1 ring-inset ring-stroke">
                      {event.kind}
                    </span>
                  </p>
                  <p className="mt-0.5 text-sm text-ink-secondary">{event.detail}</p>
                  <p className="mt-0.5 text-[11px] text-subtle">{formatTimestamp(event.ts)}</p>
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </Section>
  );
}
