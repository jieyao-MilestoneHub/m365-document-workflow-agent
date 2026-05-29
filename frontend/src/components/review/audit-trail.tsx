import { formatTimestamp } from "@/lib/format";
import type { HandoffRecord } from "@/lib/types";

/**
 * Append-only audit trail of agent state transitions (the handoff ledger). Read-only — every
 * row is one supervisor → specialist (or peer) handoff with its reason code and attempt.
 */
export function AuditTrail({ history }: { history: HandoffRecord[] }) {
  return (
    <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="text-sm font-semibold text-slate-800">Audit trail</h3>
      {history.length === 0 ? (
        <p className="text-sm text-slate-500">No handoffs recorded.</p>
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-2 py-2 font-medium">#</th>
              <th className="px-2 py-2 font-medium">From → To</th>
              <th className="px-2 py-2 font-medium">Reason</th>
              <th className="px-2 py-2 font-medium">Detail</th>
              <th className="px-2 py-2 text-right font-medium">Attempt</th>
              <th className="px-2 py-2 font-medium">When</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {history.map((h, i) => (
              <tr key={h.event_id || i}>
                <td className="px-2 py-2 tabular-nums text-slate-400">{i + 1}</td>
                <td className="px-2 py-2 text-slate-700">
                  <span className="font-medium">{h.from_role}</span>
                  <span className="mx-1 text-slate-400">→</span>
                  <span className="font-medium">{h.to_role}</span>
                </td>
                <td className="px-2 py-2">
                  <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs text-slate-600">
                    {h.reason_code}
                  </span>
                </td>
                <td className="px-2 py-2 text-slate-600">{h.detail}</td>
                <td className="px-2 py-2 text-right tabular-nums text-slate-600">{h.attempt}</td>
                <td className="px-2 py-2 text-xs text-slate-400">{formatTimestamp(h.ts)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
