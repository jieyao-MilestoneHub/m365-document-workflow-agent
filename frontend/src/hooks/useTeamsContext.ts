"use client";

import { useEffect, useState } from "react";

export type TeamsMode = "initializing" | "teams" | "standalone";

export interface TeamsState {
  mode: TeamsMode;
  /** Theme reported by the Teams host ("default" | "dark" | "contrast"), if hosted. */
  theme?: string;
}

/**
 * Initialize the Microsoft Teams SDK when hosted as a personal tab. Standalone-safe: outside
 * Teams `app.initialize()` rejects (no host), and we fall back to "standalone" so the same
 * page works in a normal browser. teams-js is imported dynamically so it never runs during SSR.
 */
export function useTeamsContext(): TeamsState {
  const [state, setState] = useState<TeamsState>({ mode: "initializing" });

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const { app } = await import("@microsoft/teams-js");
        await app.initialize();
        const context = await app.getContext();
        if (active) setState({ mode: "teams", theme: context.app.theme });
      } catch {
        // Not running inside a Teams host — render standalone.
        if (active) setState({ mode: "standalone" });
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return state;
}
