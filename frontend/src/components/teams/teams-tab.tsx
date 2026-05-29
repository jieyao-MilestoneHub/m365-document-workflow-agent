"use client";

import { InboxTable } from "@/components/inbox/inbox-table";
import { AppHeader, PageHeading } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { useTeamsContext } from "@/hooks/useTeamsContext";

/**
 * Personal-tab wrapper for the console. Hosts the approver inbox and reports whether it is
 * running inside a Teams host or standalone. The page renders identically either way; the
 * Teams SDK init is best-effort and never blocks the UI.
 */
export function TeamsTab() {
  const { mode } = useTeamsContext();
  const tone = mode === "teams" ? "positive" : "neutral";
  const label =
    mode === "initializing" ? "connecting to Teams…" : mode === "teams" ? "Teams host" : "standalone";

  return (
    <div className="flex min-h-screen flex-col">
      <AppHeader compact />
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6 sm:px-6 sm:py-8">
        <PageHeading
          eyebrow={
            <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-brand">
              Microsoft Teams personal tab
            </span>
          }
          title="Approver inbox"
          description="Process an invoice to run the three-way match agent, then open the review."
          actions={
            <Badge tone={tone} dot>
              {label}
            </Badge>
          }
        />
        <InboxTable />
      </main>
    </div>
  );
}
