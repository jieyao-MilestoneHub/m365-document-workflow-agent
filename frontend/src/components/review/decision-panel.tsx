"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckIcon, ShieldIcon } from "@/components/ui/icons";
import { Section } from "@/components/ui/section";
import type { DecisionInput } from "@/lib/api";
import { formatTimestamp } from "@/lib/format";
import type { HumanDecision } from "@/lib/types";

const INPUT =
  "w-full rounded-md border border-stroke-strong bg-surface px-3 py-2 text-sm text-ink placeholder:text-subtle focus-visible:border-brand";

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
      <Section title="Human decision" icon={CheckIcon}>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={humanDecision.action === "approve" ? "positive" : "critical"} dot>
            {humanDecision.action === "approve" ? "Approved" : "Rejected"}
          </Badge>
          <span className="text-sm text-ink-secondary">by {humanDecision.reviewer}</span>
          <span className="text-[11px] text-subtle">{formatTimestamp(humanDecision.ts)}</span>
        </div>
        {humanDecision.note ? (
          <p className="mt-2 border-l-2 border-stroke pl-2.5 text-sm italic text-muted">
            “{humanDecision.note}”
          </p>
        ) : null}
      </Section>
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
    <Section title="Approver decision" icon={ShieldIcon}>
      <div className="space-y-3">
        <input
          value={reviewer}
          onChange={(e) => setReviewer(e.target.value)}
          placeholder="Your name"
          aria-label="Reviewer name"
          className={INPUT}
        />
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Note (optional)"
          aria-label="Decision note"
          rows={2}
          className={`${INPUT} resize-none`}
        />
        {error && <p className="text-xs text-danger">{error}</p>}
        <div className="flex gap-2">
          <Button variant="success" onClick={() => submit("approve")} disabled={busy} className="flex-1">
            Approve
          </Button>
          <Button variant="danger" onClick={() => submit("reject")} disabled={busy} className="flex-1">
            Reject
          </Button>
        </div>
        <p className="text-[11px] leading-relaxed text-subtle">
          A held or escalated invoice never auto-posts — your verdict is recorded to the audit
          trail.
        </p>
      </div>
    </Section>
  );
}
