/**
 * The single API boundary (Dependency Inversion): the only module that calls fetch/EventSource.
 * Every response is validated with zod before it reaches the UI.
 */
import { z } from "zod";

import { API_BASE } from "./env";
import {
  HealthSchema,
  JobDetailSchema,
  ScenarioInfoSchema,
  StreamCompletedSchema,
  TraceEventSchema,
  type JobDetail,
  type ScenarioInfo,
  type StreamCompleted,
  type TraceEvent,
} from "./types";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, schema: z.ZodType<T>, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { Accept: "application/json", ...(init?.headers ?? {}) },
    });
  } catch (cause) {
    throw new ApiError(0, `network error reaching API: ${(cause as Error).message}`);
  }
  if (!res.ok) {
    throw new ApiError(res.status, `${res.status} ${res.statusText} on ${path}`);
  }
  return schema.parse(await res.json());
}

function jsonBody(body: unknown): RequestInit {
  return { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

export interface DecisionInput {
  action: "approve" | "reject";
  reviewer: string;
  note?: string;
}

export interface StreamHandlers {
  onTrace: (event: TraceEvent) => void;
  onCompleted: (event: StreamCompleted) => void;
  onError: (error: Error) => void;
}

/**
 * Open the reasoning-trace SSE stream. Constructing the EventSource here (not in the hook)
 * keeps this module the single network boundary (DIP). Returns a disposer the caller invokes
 * on unmount. Each event's JSON payload is zod-parsed before reaching the UI.
 */
function openStream(jobId: string, handlers: StreamHandlers): () => void {
  const source = new EventSource(`${API_BASE}/api/jobs/${encodeURIComponent(jobId)}/stream`);
  source.addEventListener("trace", (e) => {
    try {
      handlers.onTrace(TraceEventSchema.parse(JSON.parse((e as MessageEvent).data)));
    } catch (cause) {
      handlers.onError(cause as Error);
    }
  });
  source.addEventListener("completed", (e) => {
    try {
      handlers.onCompleted(StreamCompletedSchema.parse(JSON.parse((e as MessageEvent).data)));
    } catch (cause) {
      handlers.onError(cause as Error);
    } finally {
      source.close();
    }
  });
  source.onerror = () => {
    // EventSource auto-reconnects; once the server has sent `completed` we've already closed.
    if (source.readyState === EventSource.CLOSED) return;
    handlers.onError(new Error("reasoning stream connection error"));
  };
  return () => source.close();
}

export const api = {
  health: () => request("/api/health", HealthSchema),
  scenarios: (): Promise<ScenarioInfo[]> => request("/api/scenarios", z.array(ScenarioInfoSchema)),
  createJob: (invoiceRef: string): Promise<JobDetail> =>
    request("/api/jobs", JobDetailSchema, jsonBody({ invoice_ref: invoiceRef })),
  getJob: (jobId: string): Promise<JobDetail> =>
    request(`/api/jobs/${encodeURIComponent(jobId)}`, JobDetailSchema),
  decide: (jobId: string, input: DecisionInput): Promise<JobDetail> =>
    request(`/api/jobs/${encodeURIComponent(jobId)}/decision`, JobDetailSchema, jsonBody(input)),
  /** Open the reasoning-trace SSE stream; returns a disposer to close it. */
  openStream,
};
