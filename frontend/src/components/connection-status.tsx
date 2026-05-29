"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; status: string; count: number }
  | { kind: "error"; message: string };

/** Slim backend-connectivity indicator. */
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

  if (state.kind === "loading") {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-surface-muted px-3 py-1 text-xs font-medium text-muted ring-1 ring-inset ring-stroke">
        <span className="h-1.5 w-1.5 rounded-full bg-subtle pulse-dot" />
        Connecting to the agent API…
      </span>
    );
  }

  if (state.kind === "error") {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-danger-tint px-3 py-1 text-xs font-medium text-danger ring-1 ring-inset ring-danger/20">
        <span className="h-1.5 w-1.5 rounded-full bg-danger" />
        API unreachable — start the backend{" "}
        <code className="font-mono">uvicorn app.api.app:create_app --factory</code>
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-success-tint px-3 py-1 text-xs font-semibold text-success ring-1 ring-inset ring-success/20">
      <span className="h-1.5 w-1.5 rounded-full bg-success" />
      API {state.status} · {state.count} sample invoices
    </span>
  );
}
