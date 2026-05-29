import { HistoryIcon } from "@/components/ui/icons";
import { Section } from "@/components/ui/section";
import { formatTimestamp } from "@/lib/format";
import type { HandoffRecord } from "@/lib/types";

/**
 * Append-only audit trail of agent state transitions (the handoff ledger). Read-only — every
 * row is one supervisor → specialist (or peer) handoff with its reason code and attempt.
 */
export function AuditTrail({ history }: { history: HandoffRecord[] }) {
  return (
    <Section
      title="Audit trail"
      icon={HistoryIcon}
      bodyClassName={history.length === 0 ? "p-4 sm:p-5" : "p-0"}
    >
      {history.length === 0 ? (
        <p className="text-sm text-muted">No handoffs recorded.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[680px] text-left text-sm">
            <thead className="border-b border-stroke bg-surface-alt text-[11px] uppercase tracking-wide text-subtle">
              <tr>
                <th className="px-4 py-2.5 font-semibold sm:px-5">#</th>
                <th className="px-3 py-2.5 font-semibold">From → To</th>
                <th className="px-3 py-2.5 font-semibold">Reason</th>
                <th className="px-3 py-2.5 font-semibold">Detail</th>
                <th className="px-3 py-2.5 text-right font-semibold">Attempt</th>
                <th className="px-4 py-2.5 font-semibold sm:px-5">When</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stroke">
              {history.map((h, i) => (
                <tr key={h.event_id || i}>
                  <td className="px-4 py-3 tabular-nums text-subtle sm:px-5">{i + 1}</td>
                  <td className="px-3 py-3 text-ink-secondary">
                    <span className="font-semibold text-ink">{h.from_role}</span>
                    <span className="mx-1.5 text-subtle">→</span>
                    <span className="font-semibold text-ink">{h.to_role}</span>
                  </td>
                  <td className="px-3 py-3">
                    <span className="rounded bg-surface-muted px-1.5 py-0.5 font-mono text-[11px] text-muted ring-1 ring-inset ring-stroke">
                      {h.reason_code}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-ink-secondary">{h.detail}</td>
                  <td className="px-3 py-3 text-right tabular-nums text-muted">{h.attempt}</td>
                  <td className="px-4 py-3 text-[11px] text-subtle sm:px-5">
                    {formatTimestamp(h.ts)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Section>
  );
}
