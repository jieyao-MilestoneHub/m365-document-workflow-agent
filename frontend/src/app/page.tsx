import { ConnectionStatus } from "@/components/connection-status";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-3xl space-y-6 p-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">AP Three-Way Match — Agent Console</h1>
        <p className="text-slate-600">
          Copilot-native, evidence-grounded AP exception resolution. The agent recommends and
          explains; deterministic controls decide. Approver inbox and live reasoning trace coming
          next.
        </p>
      </header>
      <ConnectionStatus />
    </main>
  );
}
