import { Badge } from "@/components/ui/badge";
import { blockingReasonMeta, decisionMeta } from "@/lib/registry";
import type { Outcome } from "@/lib/types";

/** Top-of-review verdict: decision badge, summary, confidence, and blocking reasons. */
export function OutcomeBanner({ outcome }: { outcome: Outcome }) {
  const decision = decisionMeta(outcome.decision);
  return (
    <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-center gap-3">
        <Badge tone={decision.tone} title={decision.description}>
          {decision.label}
        </Badge>
        <span className="text-sm text-slate-500">
          confidence {Math.round(outcome.confidence * 100)}%
        </span>
        {outcome.escalation_target ? (
          <span className="text-sm text-slate-500">→ {outcome.escalation_target}</span>
        ) : null}
      </div>
      <p className="text-sm text-slate-700">{outcome.summary}</p>
      {outcome.blocking_reasons.length > 0 && (
        <ul className="flex flex-wrap gap-2">
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
    </section>
  );
}
