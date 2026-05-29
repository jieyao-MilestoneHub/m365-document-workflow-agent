import { Badge } from "@/components/ui/badge";
import { blockingReasonMeta, decisionMeta, type Tone } from "@/lib/registry";
import type { Outcome } from "@/lib/types";

// Decision-tone → accent treatment for the hero strip.
const ACCENT: Record<Tone, { bar: string; glow: string; ring: string; meter: string }> = {
  neutral: { bar: "bg-subtle", glow: "from-surface-muted", ring: "ring-stroke", meter: "bg-subtle" },
  positive: {
    bar: "bg-success",
    glow: "from-success-tint",
    ring: "ring-success/25",
    meter: "bg-success",
  },
  warning: {
    bar: "bg-warning",
    glow: "from-warning-tint",
    ring: "ring-warning/25",
    meter: "bg-warning",
  },
  critical: {
    bar: "bg-danger",
    glow: "from-danger-tint",
    ring: "ring-danger/25",
    meter: "bg-danger",
  },
};

/** Top-of-review verdict hero: decision, summary, confidence meter, blocking reasons. */
export function OutcomeBanner({ outcome }: { outcome: Outcome }) {
  const decision = decisionMeta(outcome.decision);
  const accent = ACCENT[decision.tone];
  const confidence = Math.round(outcome.confidence * 100);

  return (
    <section
      className={`relative overflow-hidden rounded-card border border-stroke bg-surface shadow-card ring-1 ring-inset ${accent.ring}`}
    >
      <span className={`absolute inset-y-0 left-0 w-1 ${accent.bar}`} aria-hidden="true" />
      <div
        className={`pointer-events-none absolute inset-0 bg-gradient-to-r ${accent.glow} to-transparent opacity-40`}
        aria-hidden="true"
      />
      <div className="relative grid gap-5 p-5 sm:p-6 lg:grid-cols-[1fr_auto] lg:items-center">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <Badge tone={decision.tone} dot title={decision.description}>
              {decision.label}
            </Badge>
            {outcome.escalation_target ? (
              <span className="text-sm text-muted">routed to {outcome.escalation_target}</span>
            ) : null}
          </div>
          <p className="max-w-2xl text-[15px] leading-relaxed text-ink-secondary">
            {outcome.summary}
          </p>
          {outcome.blocking_reasons.length > 0 && (
            <ul className="flex flex-wrap gap-2 pt-1">
              {outcome.blocking_reasons.map((code) => {
                const meta = blockingReasonMeta(code);
                return (
                  <li key={code}>
                    <Badge tone={meta.tone} title={meta.help}>
                      {meta.label}
                    </Badge>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div className="w-full sm:w-52">
          <div className="flex items-baseline justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-subtle">
              Agent confidence
            </span>
            <span className="font-display text-xl font-semibold tabular-nums text-ink">
              {confidence}%
            </span>
          </div>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-muted">
            <div
              className={`h-full rounded-full ${accent.meter}`}
              style={{ width: `${confidence}%` }}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
