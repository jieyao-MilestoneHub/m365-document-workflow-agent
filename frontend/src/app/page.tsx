import { ConnectionStatus } from "@/components/connection-status";
import { InboxTable } from "@/components/inbox/inbox-table";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-5xl space-y-6 p-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">AP Three-Way Match — Agent Console</h1>
        <p className="text-slate-600">
          Copilot-native, evidence-grounded AP exception resolution. The agent recommends and
          explains; deterministic controls decide. Process an invoice to run the three-way match,
          then open the review to see the canvas, variance evidence, GL preview and live reasoning
          trace.
        </p>
      </header>
      <ConnectionStatus />
      <section className="space-y-3">
        <h2 className="text-lg font-semibold tracking-tight">Approver inbox</h2>
        <InboxTable />
      </section>
    </main>
  );
}
