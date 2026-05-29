import { ConnectionStatus } from "@/components/connection-status";
import { InboxTable } from "@/components/inbox/inbox-table";
import { AppShell, PageHeading } from "@/components/shell/app-shell";

export default function Home() {
  return (
    <AppShell>
      <PageHeading
        eyebrow={
          <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-brand">
            Exception queue
          </span>
        }
        title="Approver inbox"
        description="Evidence-grounded AP exception resolution. The agent recommends and explains; deterministic controls decide. Process an invoice to run the three-way match, then open the review for the canvas, variance evidence, GL preview and live reasoning trace."
        actions={<ConnectionStatus />}
      />
      <InboxTable />
    </AppShell>
  );
}
