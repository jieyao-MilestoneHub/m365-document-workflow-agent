"use client";

import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
import { InboxIcon } from "@/components/ui/icons";
import { Section } from "@/components/ui/section";
import { useJobRunner } from "@/hooks/useJobRunner";
import { useScenarios } from "@/hooks/useScenarios";
import { formatMoney } from "@/lib/format";
import { decisionMeta } from "@/lib/registry";

/** Approver inbox: list sample invoices, run the agent, surface the resulting decision. */
export function InboxTable() {
  const { state, reload } = useScenarios();
  const { runs, process } = useJobRunner();

  if (state.status === "loading") {
    return (
      <Section title="Invoices" icon={InboxIcon}>
        <div className="space-y-2.5">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-12 animate-pulse rounded-md bg-surface-muted" />
          ))}
        </div>
      </Section>
    );
  }

  if (state.status === "error") {
    return (
      <Section title="Invoices" icon={InboxIcon}>
        <div className="rounded-md bg-danger-tint px-4 py-3 text-sm text-danger ring-1 ring-inset ring-danger/20">
          <p>Could not load invoices — is the backend running on port 8000? ({state.message})</p>
          <Button variant="danger" size="sm" className="mt-3" onClick={reload}>
            Retry
          </Button>
        </div>
      </Section>
    );
  }

  return (
    <Section
      title="Invoices"
      icon={InboxIcon}
      aside={
        <span className="text-xs font-medium text-muted">
          {state.data.length} pending {state.data.length === 1 ? "invoice" : "invoices"}
        </span>
      }
      bodyClassName="p-0"
    >
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="border-b border-stroke bg-surface-alt text-[11px] uppercase tracking-wide text-subtle">
            <tr>
              <th className="px-4 py-2.5 font-semibold sm:px-5">Invoice</th>
              <th className="px-4 py-2.5 font-semibold">Vendor</th>
              <th className="px-4 py-2.5 text-right font-semibold">Total</th>
              <th className="px-4 py-2.5 font-semibold">Result</th>
              <th className="px-4 py-2.5 text-right font-semibold sm:px-5">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-stroke">
            {state.data.map((scenario, i) => {
              const run = runs[scenario.id] ?? { status: "idle" as const };
              return (
                <tr
                  key={scenario.id}
                  className="rise transition-colors hover:bg-brand-tint/40"
                  style={{ ["--d" as string]: `${i * 45}ms` }}
                >
                  <td className="px-4 py-3 sm:px-5">
                    <span className="font-mono text-[13px] font-semibold text-ink">
                      {scenario.id}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-ink-secondary">{scenario.vendor}</td>
                  <td className="px-4 py-3 text-right tabular-nums text-ink-secondary">
                    {formatMoney(scenario.total, scenario.currency)}
                  </td>
                  <td className="px-4 py-3">
                    {run.status === "done" ? (
                      (() => {
                        const meta = decisionMeta(run.job.decision);
                        return (
                          <Badge tone={meta.tone} dot title={meta.description}>
                            {meta.label}
                          </Badge>
                        );
                      })()
                    ) : run.status === "error" ? (
                      <span className="text-xs text-danger">{run.message}</span>
                    ) : (
                      <span className="text-xs text-subtle">Not run</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right sm:px-5">
                    {run.status === "done" ? (
                      <ButtonLink href={`/review/${run.job.job_id}`} variant="default" size="sm">
                        Review
                      </ButtonLink>
                    ) : (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => process(scenario.id)}
                        disabled={run.status === "running"}
                      >
                        {run.status === "running" ? "Processing…" : "Process"}
                      </Button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Section>
  );
}
