"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; status: string; count: number }
  | { kind: "error"; message: string };

export function ConnectionStatus() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [health, scenarios] = await Promise.all([api.health(), api.scenarios()]);
        if (active) setState({ kind: "ok", status: health.status, count: scenarios.length });
      } catch (error) {
        if (active) {
          setState({ kind: "error", message: error instanceof Error ? error.message : "unknown" });
        }
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  if (state.kind === "loading") return <p className="text-slate-500">Connecting to the agent API…</p>;
  if (state.kind === "error") {
    return (
      <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
        API unreachable — start the backend with{" "}
        <code className="font-mono">uvicorn app.api.app:create_app --factory</code>. ({state.message})
      </p>
    );
  }
  return (
    <p className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
      API {state.status} · {state.count} sample invoices available
    </p>
  );
}
