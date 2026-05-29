"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { useJobRunner } from "@/hooks/useJobRunner";
import { useScenarios } from "@/hooks/useScenarios";
import { formatMoney } from "@/lib/format";
import { decisionMeta } from "@/lib/registry";

/** Approver inbox: list sample invoices, run the agent, surface the resulting decision. */
export function InboxTable() {
  const { state, reload } = useScenarios();
  const { runs, process } = useJobRunner();

  if (state.status === "loading") {
    return <p className="text-slate-500">Loading invoices…</p>;
  }
  if (state.status === "error") {
    return (
      <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
        <p>Could not load invoices — is the backend running on port 8000? ({state.message})</p>
        <button
          onClick={reload}
          className="mt-2 rounded bg-red-600 px-3 py-1 text-xs font-medium text-white hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3 font-medium">Invoice</th>
            <th className="px-4 py-3 font-medium">Vendor</th>
            <th className="px-4 py-3 text-right font-medium">Total</th>
            <th className="px-4 py-3 font-medium">Result</th>
            <th className="px-4 py-3 font-medium">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {state.data.map((scenario) => {
            const run = runs[scenario.id] ?? { status: "idle" as const };
            return (
              <tr key={scenario.id} className="hover:bg-slate-50/60">
                <td className="px-4 py-3 font-mono font-medium text-slate-800">{scenario.id}</td>
                <td className="px-4 py-3 text-slate-700">{scenario.vendor}</td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                  {formatMoney(scenario.total, scenario.currency)}
                </td>
                <td className="px-4 py-3">
                  {run.status === "done" ? (
                    (() => {
                      const meta = decisionMeta(run.job.decision);
                      return (
                        <Badge tone={meta.tone} title={meta.description}>
                          {meta.label}
                        </Badge>
                      );
                    })()
                  ) : run.status === "error" ? (
                    <span className="text-xs text-red-600">{run.message}</span>
                  ) : (
                    <span className="text-xs text-slate-400">—</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {run.status === "done" ? (
                    <Link
                      href={`/review/${run.job.job_id}`}
                      className="rounded bg-slate-900 px-3 py-1 text-xs font-medium text-white hover:bg-slate-700"
                    >
                      Review
                    </Link>
                  ) : (
                    <button
                      onClick={() => process(scenario.id)}
                      disabled={run.status === "running"}
                      className="rounded bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                    >
                      {run.status === "running" ? "Processing…" : "Process"}
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
