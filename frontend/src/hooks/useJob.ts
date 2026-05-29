"use client";

import { useCallback, useEffect, useState } from "react";

import { api, type DecisionInput } from "@/lib/api";
import type { JobDetail } from "@/lib/types";

import type { AsyncState } from "./useScenarios";

/** Loads a single job by id and exposes a `decide` action that refreshes the local copy. */
export function useJob(jobId: string | undefined) {
  const [state, setState] = useState<AsyncState<JobDetail>>({ status: "loading" });
  const [trackedId, setTrackedId] = useState(jobId);

  // Reset to loading during render when the job changes (avoids setState-in-effect).
  if (trackedId !== jobId) {
    setTrackedId(jobId);
    setState({ status: "loading" });
  }

  useEffect(() => {
    if (!jobId) return;
    let active = true;
    (async () => {
      try {
        const data = await api.getJob(jobId);
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
  }, [jobId]);

  const decide = useCallback(
    async (input: DecisionInput) => {
      if (!jobId) throw new Error("no job to decide on");
      const updated = await api.decide(jobId, input);
      setState({ status: "ready", data: updated });
      return updated;
    },
    [jobId],
  );

  return { state, decide };
}
