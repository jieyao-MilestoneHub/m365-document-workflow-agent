/**
 * Zod schemas mirroring the backend API contract (`backend/app/schemas/*.py`).
 *
 * Parsing every response through these (in `lib/api.ts`) is both the SOLID seam and a
 * security control: the UI never renders unvalidated data.
 *
 * Money/quantity fields are JSON strings — the backend dumps `Decimal` with pydantic's
 * json mode, so they arrive as strings. Parse with `Number()` only for display math; keep
 * the string for exact display. Dates are ISO strings.
 */
import { z } from "zod";

// ---- closed enums (mirror app/schemas/enums.py) ----------------------------------------

export const DecisionSchema = z.enum(["pass", "hold", "escalate"]);
export type Decision = z.infer<typeof DecisionSchema>;

export const SeveritySchema = z.enum(["none", "low", "medium", "high"]);
export type Severity = z.infer<typeof SeveritySchema>;

export const LineStatusSchema = z.enum([
  "matched",
  "quantity_variance",
  "price_variance",
  "unit_variance",
  "missing_in_po",
  "missing_in_grn",
  "no_po_line",
  "unmatched",
]);
export type LineStatus = z.infer<typeof LineStatusSchema>;

export const MatchStatusSchema = z.enum([
  "matched",
  "partial",
  "missing_po",
  "missing_grn",
  "mismatch",
]);
export type MatchStatus = z.infer<typeof MatchStatusSchema>;

export const PostingDirectionSchema = z.enum(["debit", "credit"]);
export type PostingDirection = z.infer<typeof PostingDirectionSchema>;

// ---- primitives ------------------------------------------------------------------------

export const HealthSchema = z.object({ status: z.string() });

export const ScenarioInfoSchema = z.object({
  id: z.string(),
  vendor: z.string(),
  total: z.string(),
  currency: z.string(),
});
export type ScenarioInfo = z.infer<typeof ScenarioInfoSchema>;

/** One SSE `trace` event (also persisted in JobDetail.events). */
export const TraceEventSchema = z.object({
  seq: z.number(),
  kind: z.string(),
  role: z.string(),
  detail: z.string(),
  ts: z.string(),
});
export type TraceEvent = z.infer<typeof TraceEventSchema>;

/** Terminal SSE `completed` event. */
export const StreamCompletedSchema = z.object({
  job_id: z.string(),
  decision: DecisionSchema,
  summary: z.string(),
  blocking_reasons: z.array(z.string()),
});
export type StreamCompleted = z.infer<typeof StreamCompletedSchema>;

export const CitationSchema = z.object({
  document_id: z.string(),
  document_title: z.string(),
  cited_text: z.string(),
  page: z.number().nullable().optional(),
  start_char: z.number().nullable().optional(),
  end_char: z.number().nullable().optional(),
});
export type Citation = z.infer<typeof CitationSchema>;

// ---- outcome (app/schemas/outcome.py) --------------------------------------------------

export const ExceptionTicketSchema = z.object({
  ticket_id: z.string(),
  // blocking-reason code: left as a string so new codes render via the OCP registry
  exception_type: z.string(),
  severity: SeveritySchema,
  affected_lines: z.array(z.number()).default([]),
  suggested_resolution: z.string().nullable().optional(),
  requires_human: z.boolean().default(true),
  evidence: z.record(z.string(), z.unknown()).default({}),
});
export type ExceptionTicket = z.infer<typeof ExceptionTicketSchema>;

export const OutcomeSchema = z.object({
  invoice_number: z.string(),
  decision: DecisionSchema,
  confidence: z.number(),
  // blocking reasons are open by design — rendered through BLOCKING_REASON_META (OCP)
  blocking_reasons: z.array(z.string()),
  summary: z.string(),
  escalation_target: z.string().nullable().optional(),
  exception_tickets: z.array(ExceptionTicketSchema).default([]),
});
export type Outcome = z.infer<typeof OutcomeSchema>;

// ---- invoice (app/schemas/invoice.py) --------------------------------------------------

export const InvoiceLineItemSchema = z.object({
  line_no: z.number(),
  sku: z.string().nullable().optional(),
  description: z.string(),
  quantity: z.string(),
  unit_price: z.string(),
  line_total: z.string(),
  tax_rate: z.string().nullable().optional(),
});
export type InvoiceLineItem = z.infer<typeof InvoiceLineItemSchema>;

export const VendorInvoiceSchema = z.object({
  vendor_name: z.string(),
  vendor_id: z.string().nullable().optional(),
  invoice_number: z.string(),
  invoice_date: z.string(),
  due_date: z.string().nullable().optional(),
  currency: z.string(),
  subtotal: z.string(),
  tax_total: z.string(),
  total: z.string(),
  po_ref: z.string().nullable().optional(),
  grn_ref: z.string().nullable().optional(),
  line_items: z.array(InvoiceLineItemSchema).default([]),
  missing_fields: z.array(z.string()).default([]),
});
export type VendorInvoice = z.infer<typeof VendorInvoiceSchema>;

// ---- match (app/schemas/match.py) ------------------------------------------------------

export const LineMatchSchema = z.object({
  invoice_line_no: z.number(),
  po_line_idx: z.number().nullable().optional(),
  grn_line_idx: z.number().nullable().optional(),
  po_unit_price: z.string().nullable().optional(),
  status: LineStatusSchema,
  quantity_delta: z.string().default("0"),
  price_delta: z.string().default("0"),
  within_tolerance: z.boolean().default(true),
  received_quantity: z.string().nullable().optional(),
  invoiced_to_date_quantity: z.string().default("0"),
  remaining_billable_quantity: z.string().nullable().optional(),
  over_billed: z.boolean().default(false),
  resolved_sku: z.string().nullable().optional(),
  alias_unresolved: z.boolean().default(false),
  note: z.string().nullable().optional(),
});
export type LineMatch = z.infer<typeof LineMatchSchema>;

export const ThreeWayMatchReportSchema = z.object({
  invoice_number: z.string(),
  po_number: z.string().nullable().optional(),
  grn_number: z.string().nullable().optional(),
  match_status: MatchStatusSchema,
  lines: z.array(LineMatchSchema).default([]),
  po_currency: z.string().nullable().optional(),
  currency_mismatch: z.boolean().default(false),
  tolerance_version: z.string().default(""),
  citations: z.array(CitationSchema).default([]),
});
export type ThreeWayMatchReport = z.infer<typeof ThreeWayMatchReportSchema>;

// ---- variance (app/schemas/variance.py) ------------------------------------------------

export const LineVarianceSchema = z.object({
  invoice_line_no: z.number(),
  financial_impact: z.string(),
  severity: SeveritySchema,
  within_tolerance: z.boolean(),
  rationale: z.string().nullable().optional(),
});
export type LineVariance = z.infer<typeof LineVarianceSchema>;

export const VarianceReportSchema = z.object({
  invoice_number: z.string(),
  lines: z.array(LineVarianceSchema).default([]),
  overall_severity: SeveritySchema.default("none"),
  financial_impact_total: z.string().default("0"),
  thresholds_version: z.string().default(""),
});
export type VarianceReport = z.infer<typeof VarianceReportSchema>;

// ---- posting (app/schemas/posting.py) --------------------------------------------------

export const PostingLineSchema = z.object({
  gl_account: z.string(),
  direction: PostingDirectionSchema,
  amount: z.string(),
  memo: z.string().nullable().optional(),
});
export type PostingLine = z.infer<typeof PostingLineSchema>;

export const PostingDraftSchema = z.object({
  invoice_number: z.string(),
  currency: z.string(),
  lines: z.array(PostingLineSchema).default([]),
  balanced: z.boolean().default(false),
  notes: z.array(z.string()).default([]),
  gl_map_version: z.string().default(""),
});
export type PostingDraft = z.infer<typeof PostingDraftSchema>;

// ---- audit / human decision ------------------------------------------------------------

export const HandoffRecordSchema = z.object({
  from_role: z.string(),
  to_role: z.string(),
  reason_code: z.string(),
  detail: z.string(),
  attempt: z.number(),
  event_id: z.string(),
  ts: z.string(),
});
export type HandoffRecord = z.infer<typeof HandoffRecordSchema>;

export const HumanDecisionSchema = z.object({
  action: z.enum(["approve", "reject"]),
  reviewer: z.string(),
  note: z.string().nullable().optional(),
  ts: z.string(),
});
export type HumanDecision = z.infer<typeof HumanDecisionSchema>;

// ---- job detail ------------------------------------------------------------------------

export const JobDetailSchema = z.object({
  job_id: z.string(),
  invoice_ref: z.string(),
  status: z.string(),
  decision: DecisionSchema,
  outcome: OutcomeSchema,
  invoice: VendorInvoiceSchema.nullable(),
  match: ThreeWayMatchReportSchema.nullable(),
  variance: VarianceReportSchema.nullable(),
  posting: PostingDraftSchema.nullable(),
  // exception_reviewer payload — shape overlaps the outcome; kept opaque (not rendered directly)
  review: z.unknown().nullable(),
  handoff_history: z.array(HandoffRecordSchema).default([]),
  events: z.array(TraceEventSchema).default([]),
  human_decision: HumanDecisionSchema.nullable(),
});
export type JobDetail = z.infer<typeof JobDetailSchema>;
