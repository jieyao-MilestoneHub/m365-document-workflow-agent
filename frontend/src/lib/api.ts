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
  type JobDetail,
  type ScenarioInfo,
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

export const api = {
  health: () => request("/api/health", HealthSchema),
  scenarios: (): Promise<ScenarioInfo[]> => request("/api/scenarios", z.array(ScenarioInfoSchema)),
  createJob: (invoiceRef: string): Promise<JobDetail> =>
    request("/api/jobs", JobDetailSchema, jsonBody({ invoice_ref: invoiceRef })),
  getJob: (jobId: string): Promise<JobDetail> =>
    request(`/api/jobs/${encodeURIComponent(jobId)}`, JobDetailSchema),
  decide: (jobId: string, input: DecisionInput): Promise<JobDetail> =>
    request(`/api/jobs/${encodeURIComponent(jobId)}/decision`, JobDetailSchema, jsonBody(input)),
  /** SSE endpoint URL; the EventSource is created in the client hook. */
  streamUrl: (jobId: string): string => `${API_BASE}/api/jobs/${encodeURIComponent(jobId)}/stream`,
};
