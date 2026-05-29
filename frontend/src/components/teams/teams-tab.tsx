"use client";

import { InboxTable } from "@/components/inbox/inbox-table";
import { Badge } from "@/components/ui/badge";
import { useTeamsContext } from "@/hooks/useTeamsContext";

/**
 * Personal-tab wrapper for the console. Hosts the approver inbox and reports whether it is
 * running inside a Teams host or standalone. The page renders identically either way; the
 * Teams SDK init is best-effort and never blocks the UI.
 */
export function TeamsTab() {
  const { mode } = useTeamsContext();

  return (
    <main className="mx-auto w-full max-w-5xl space-y-6 p-8">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">AP Three-Way Match</h1>
          <p className="text-sm text-slate-600">Approver inbox — Microsoft Teams personal tab.</p>
        </div>
        <Badge tone={mode === "teams" ? "positive" : "neutral"}>
          {mode === "initializing"
            ? "connecting to Teams…"
            : mode === "teams"
              ? "Teams host"
              : "standalone"}
        </Badge>
      </header>
      <InboxTable />
    </main>
  );
}
