"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import type { DecisionInput } from "@/lib/api";
import { formatTimestamp } from "@/lib/format";
import type { HumanDecision } from "@/lib/types";

/**
 * Approve/Reject panel. Calls the supplied `onDecide` (wired to api.decide via the useJob
 * hook) and reflects the recorded human_decision. The agent never auto-posts a held invoice —
 * a human verdict is required here.
 */
export function DecisionPanel({
  humanDecision,
  onDecide,
}: {
  humanDecision: HumanDecision | null;
  onDecide: (input: DecisionInput) => Promise<unknown>;
}) {
  const [reviewer, setReviewer] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (humanDecision) {
    return (
      <section className="space-y-2 rounded-lg border border-slate-200 bg-white p-5">
        <h3 className="text-sm font-semibold text-slate-800">Human decision</h3>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={humanDecision.action === "approve" ? "positive" : "critical"}>
            {humanDecision.action === "approve" ? "Approved" : "Rejected"}
          </Badge>
          <span className="text-sm text-slate-600">by {humanDecision.reviewer}</span>
          <span className="text-xs text-slate-400">{formatTimestamp(humanDecision.ts)}</span>
        </div>
        {humanDecision.note ? (
          <p className="text-sm text-slate-600">“{humanDecision.note}”</p>
        ) : null}
      </section>
    );
  }

  async function submit(action: "approve" | "reject") {
    if (!reviewer.trim()) {
      setError("Enter your name to record the decision.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await onDecide({ action, reviewer: reviewer.trim(), note: note.trim() || undefined });
    } catch (e) {
      setError(e instanceof Error ? e.message : "could not record decision");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="text-sm font-semibold text-slate-800">Approver decision</h3>
      <div className="grid gap-2 sm:grid-cols-2">
        <input
          value={reviewer}
          onChange={(e) => setReviewer(e.target.value)}
          placeholder="Your name"
          aria-label="Reviewer name"
          className="rounded border border-slate-300 px-3 py-2 text-sm"
        />
        <input
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Note (optional)"
          aria-label="Decision note"
          className="rounded border border-slate-300 px-3 py-2 text-sm"
        />
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button
          onClick={() => submit("approve")}
          disabled={busy}
          className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          Approve
        </button>
        <button
          onClick={() => submit("reject")}
          disabled={busy}
          className="rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
        >
          Reject
        </button>
      </div>
    </section>
  );
}
