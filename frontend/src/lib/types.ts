/**
 * Zod schemas mirroring the backend API contract.
 *
 * Parsing every response through these (in `lib/api.ts`) is both the SOLID seam and a
 * security control: the UI never renders unvalidated data. Nested invoice/match/variance/
 * posting payloads are typed loosely here and refined per surface in later PRs.
 */
import { z } from "zod";

export const DecisionSchema = z.enum(["pass", "hold", "escalate"]);
export type Decision = z.infer<typeof DecisionSchema>;

export const HealthSchema = z.object({ status: z.string() });

export const ScenarioInfoSchema = z.object({
  id: z.string(),
  vendor: z.string(),
  total: z.string(),
  currency: z.string(),
});
export type ScenarioInfo = z.infer<typeof ScenarioInfoSchema>;

export const TraceEventSchema = z.object({
  seq: z.number(),
  kind: z.string(),
  role: z.string(),
  detail: z.string(),
  ts: z.string(),
});
export type TraceEvent = z.infer<typeof TraceEventSchema>;

export const OutcomeSchema = z.object({
  invoice_number: z.string(),
  decision: DecisionSchema,
  confidence: z.number(),
  blocking_reasons: z.array(z.string()),
  summary: z.string(),
  escalation_target: z.string().nullable().optional(),
  exception_tickets: z.array(z.unknown()).default([]),
});
export type Outcome = z.infer<typeof OutcomeSchema>;

export const JobDetailSchema = z.object({
  job_id: z.string(),
  invoice_ref: z.string(),
  status: z.string(),
  decision: DecisionSchema,
  outcome: OutcomeSchema,
  // refined into typed schemas in PR17–19 (canvas / variance / posting)
  invoice: z.unknown().nullable(),
  match: z.unknown().nullable(),
  variance: z.unknown().nullable(),
  posting: z.unknown().nullable(),
  review: z.unknown().nullable(),
  handoff_history: z.array(z.unknown()),
  events: z.array(TraceEventSchema),
  human_decision: z.unknown().nullable(),
});
export type JobDetail = z.infer<typeof JobDetailSchema>;
