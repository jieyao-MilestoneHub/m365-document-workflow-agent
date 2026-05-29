"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { DecisionPanel } from "@/components/review/decision-panel";
import { GLJournalPreview } from "@/components/review/gl-journal-preview";
import { OutcomeBanner } from "@/components/review/outcome-banner";
import { AgentReasoningTrace } from "@/components/review/reasoning-trace";
import { ThreeWayMatchCanvas } from "@/components/review/three-way-canvas";
import { VarianceEvidenceTable } from "@/components/review/variance-table";
import { useJob } from "@/hooks/useJob";

export default function ReviewPage() {
  // Read the route param on the client — Next 16 server `params` are async; this page is a
  // client component because it streams (SSE) and posts decisions.
  const params = useParams<{ id: string }>();
  const jobId = typeof params.id === "string" ? params.id : undefined;
  const { state, decide } = useJob(jobId);

  return (
    <main className="mx-auto w-full max-w-5xl space-y-6 p-8">
      <Link href="/" className="text-sm text-blue-600 hover:underline">
        ← Back to inbox
      </Link>

      {state.status === "loading" && <p className="text-slate-500">Loading job…</p>}
      {state.status === "error" && (
        <p className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          Could not load job {jobId} — {state.message}
        </p>
      )}

      {state.status === "ready" &&
        (() => {
          const job = state.data;
          const currency = job.invoice?.currency ?? "USD";
          return (
            <>
              <header className="space-y-1">
                <h1 className="text-2xl font-semibold tracking-tight">
                  Review {job.invoice_ref}
                </h1>
                <p className="text-sm text-slate-500">
                  {job.invoice?.vendor_name ?? "—"} · job{" "}
                  <span className="font-mono">{job.job_id}</span>
                </p>
              </header>

              <OutcomeBanner outcome={job.outcome} />
              <ThreeWayMatchCanvas invoice={job.invoice} match={job.match} />
              <VarianceEvidenceTable variance={job.variance} currency={currency} />
              <GLJournalPreview posting={job.posting} />
              {jobId && <AgentReasoningTrace jobId={jobId} />}
              <DecisionPanel humanDecision={job.human_decision} onDecide={decide} />
            </>
          );
        })()}
    </main>
  );
}
