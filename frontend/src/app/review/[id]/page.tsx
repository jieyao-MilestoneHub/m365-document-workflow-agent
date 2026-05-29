"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { AppShell, PageHeading } from "@/components/shell/app-shell";
import { AuditTrail } from "@/components/review/audit-trail";
import { DecisionPanel } from "@/components/review/decision-panel";
import { GLJournalPreview } from "@/components/review/gl-journal-preview";
import { OutcomeBanner } from "@/components/review/outcome-banner";
import { AgentReasoningTrace } from "@/components/review/reasoning-trace";
import { ThreeWayMatchCanvas } from "@/components/review/three-way-canvas";
import { VarianceEvidenceTable } from "@/components/review/variance-table";
import { VendorPolicyPanel } from "@/components/review/vendor-policy";
import { useJob } from "@/hooks/useJob";

export default function ReviewPage() {
  // Read the route param on the client — Next 16 server `params` are async; this page is a
  // client component because it streams (SSE) and posts decisions.
  const params = useParams<{ id: string }>();
  const jobId = typeof params.id === "string" ? params.id : undefined;
  const { state, decide } = useJob(jobId);

  return (
    <AppShell>
      <Link
        href="/"
        className="mb-4 inline-flex items-center gap-1 text-sm font-medium text-brand hover:text-brand-hover"
      >
        <span aria-hidden="true">←</span> Back to inbox
      </Link>

      {state.status === "loading" && (
        <div className="space-y-4">
          <div className="h-28 animate-pulse rounded-card bg-surface-muted" />
          <div className="h-64 animate-pulse rounded-card bg-surface-muted" />
        </div>
      )}

      {state.status === "error" && (
        <p className="rounded-card bg-danger-tint px-4 py-3 text-sm text-danger ring-1 ring-inset ring-danger/20">
          Could not load job {jobId} — {state.message}
        </p>
      )}

      {state.status === "ready" &&
        (() => {
          const job = state.data;
          const currency = job.invoice?.currency ?? "USD";
          return (
            <div className="space-y-5">
              <PageHeading
                eyebrow={
                  <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-brand">
                    Three-way match review
                  </span>
                }
                title={`Review ${job.invoice_ref}`}
                description={
                  <>
                    {job.invoice?.vendor_name ?? "—"} · job{" "}
                    <span className="font-mono text-ink-secondary">{job.job_id}</span>
                  </>
                }
              />

              <OutcomeBanner outcome={job.outcome} />

              <div className="grid gap-5 lg:grid-cols-3">
                <div className="space-y-5 lg:col-span-2">
                  <ThreeWayMatchCanvas invoice={job.invoice} match={job.match} />
                  <VarianceEvidenceTable variance={job.variance} currency={currency} />
                  <GLJournalPreview posting={job.posting} />
                  {jobId && <AgentReasoningTrace jobId={jobId} />}
                  <AuditTrail history={job.handoff_history} />
                </div>

                <aside className="space-y-5">
                  <div className="space-y-5 lg:sticky lg:top-20">
                    <VendorPolicyPanel job={job} />
                    <DecisionPanel humanDecision={job.human_decision} onDecide={decide} />
                  </div>
                </aside>
              </div>
            </div>
          );
        })()}
    </AppShell>
  );
}
