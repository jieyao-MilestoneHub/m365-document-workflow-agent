"use client";

import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { ScenarioInfo } from "@/lib/types";

export type AsyncState<T> =
  | { status: "loading" }
  | { status: "ready"; data: T }
  | { status: "error"; message: string };

/** Loads the inbox scenario list via the api boundary. Components never fetch directly. */
export function useScenarios() {
  const [state, setState] = useState<AsyncState<ScenarioInfo[]>>({ status: "loading" });

  const load = useCallback(async () => {
    setState({ status: "loading" });
    try {
      setState({ status: "ready", data: await api.scenarios() });
    } catch (error) {
      setState({ status: "error", message: error instanceof Error ? error.message : "unknown" });
    }
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const data = await api.scenarios();
        if (active) setState({ status: "ready", data });
      } catch (error) {
        if (active) {
          setState({ status: "error", message: error instanceof Error ? error.message : "unknown" });
        }
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return { state, reload: load };
}
