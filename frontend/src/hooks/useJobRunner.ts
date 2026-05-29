"use client";

import { useCallback, useState } from "react";

import { api } from "@/lib/api";
import type { JobDetail } from "@/lib/types";

export type RunState =
  | { status: "idle" }
  | { status: "running" }
  | { status: "done"; job: JobDetail }
  | { status: "error"; message: string };

/**
 * Tracks per-invoice "Process" runs for the inbox. Keeps the createJob call inside a hook so
 * the table component stays presentational and never touches the network directly.
 */
export function useJobRunner() {
  const [runs, setRuns] = useState<Record<string, RunState>>({});

  const process = useCallback(async (invoiceRef: string) => {
    setRuns((prev) => ({ ...prev, [invoiceRef]: { status: "running" } }));
    try {
      const job = await api.createJob(invoiceRef);
      setRuns((prev) => ({ ...prev, [invoiceRef]: { status: "done", job } }));
      return job;
    } catch (error) {
      const message = error instanceof Error ? error.message : "unknown error";
      setRuns((prev) => ({ ...prev, [invoiceRef]: { status: "error", message } }));
      return null;
    }
  }, []);

  return { runs, process };
}
