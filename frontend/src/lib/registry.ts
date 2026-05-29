/**
 * Presentation registries (Open/Closed): map backend codes → display metadata. Adding a new
 * blocking reason, decision, severity or line status means adding one entry here — no
 * component changes. Components look codes up through the `*Meta` helpers, which always return
 * a safe fallback so an unknown code renders as plain text rather than crashing.
 */
import type { Decision, LineStatus, Severity } from "./types";

export type Tone = "neutral" | "positive" | "warning" | "critical";

export interface DecisionMeta {
  label: string;
  tone: Tone;
  description: string;
}

export const DECISION_BADGE: Record<Decision, DecisionMeta> = {
  pass: { label: "Pass", tone: "positive", description: "Cleared all controls — safe to post." },
  hold: { label: "Hold", tone: "warning", description: "Held for approver review before posting." },
  escalate: {
    label: "Escalate",
    tone: "critical",
    description: "Routed to a human owner — cannot auto-resolve.",
  },
};

export function decisionMeta(decision: string): DecisionMeta {
  return (
    DECISION_BADGE[decision as Decision] ?? {
      label: decision,
      tone: "neutral",
      description: "",
    }
  );
}

export interface SeverityMeta {
  label: string;
  tone: Tone;
}

export const SEVERITY_META: Record<Severity, SeverityMeta> = {
  none: { label: "None", tone: "neutral" },
  low: { label: "Low", tone: "positive" },
  medium: { label: "Medium", tone: "warning" },
  high: { label: "High", tone: "critical" },
};

export function severityMeta(severity: string): SeverityMeta {
  return SEVERITY_META[severity as Severity] ?? { label: severity, tone: "neutral" };
}

export interface LineStatusMeta {
  label: string;
  tone: Tone;
}

export const LINE_STATUS_META: Record<LineStatus, LineStatusMeta> = {
  matched: { label: "Matched", tone: "positive" },
  quantity_variance: { label: "Qty variance", tone: "warning" },
  price_variance: { label: "Price variance", tone: "warning" },
  unit_variance: { label: "Unit variance", tone: "warning" },
  missing_in_po: { label: "Missing in PO", tone: "critical" },
  missing_in_grn: { label: "Missing in GRN", tone: "critical" },
  no_po_line: { label: "No PO line", tone: "critical" },
  unmatched: { label: "Unmatched", tone: "critical" },
};

export function lineStatusMeta(status: string): LineStatusMeta {
  return LINE_STATUS_META[status as LineStatus] ?? { label: status, tone: "neutral" };
}

export interface BlockingReasonMeta {
  label: string;
  tone: Tone;
  help: string;
}

/**
 * Mirrors `BlockingReason` in app/schemas/enums.py. Codes outside this map still render via
 * `blockingReasonMeta`'s fallback, so the backend can add reasons without breaking the UI.
 */
export const BLOCKING_REASON_META: Record<string, BlockingReasonMeta> = {
  MISSING_INVOICE_UPSTREAM: {
    label: "Missing invoice data",
    tone: "critical",
    help: "The invoice could not be extracted upstream.",
  },
  MISSING_THREE_WAY_MATCH_UPSTREAM: {
    label: "Missing match data",
    tone: "critical",
    help: "The three-way match did not run.",
  },
  INVOICE_QUALITY_FAIL: {
    label: "Invoice quality failure",
    tone: "critical",
    help: "Extraction confidence too low to proceed.",
  },
  THREE_WAY_MATCH_INCOMPLETE: {
    label: "Match incomplete",
    tone: "warning",
    help: "PO or GRN coverage is missing for one or more lines.",
  },
  THREE_WAY_MATCH_VARIANCE: {
    label: "Match variance",
    tone: "warning",
    help: "Lines differ from the PO/GRN beyond an exact match.",
  },
  VARIANCE_HIGH_SEVERITY: {
    label: "High-severity variance",
    tone: "critical",
    help: "Financial impact is large enough to require escalation.",
  },
  VARIANCE_OUTSIDE_TOLERANCE: {
    label: "Variance outside tolerance",
    tone: "warning",
    help: "A line exceeds the configured price/quantity tolerance.",
  },
  POSTING_DRAFT_UNBALANCED: {
    label: "Posting unbalanced",
    tone: "critical",
    help: "Debits do not equal credits — never auto-posts.",
  },
  GL_ACCOUNT_INVALID: {
    label: "Invalid GL account",
    tone: "critical",
    help: "A posting line references an unknown GL account.",
  },
  POSTING_PERIOD_CLOSED: {
    label: "Period closed",
    tone: "critical",
    help: "The accounting period for this posting is closed.",
  },
  VENDOR_ON_HOLD_LIST: {
    label: "Vendor on hold",
    tone: "critical",
    help: "The vendor is on the payment-hold list.",
  },
  VENDOR_GRAY_ZONE: {
    label: "Vendor gray zone",
    tone: "warning",
    help: "Vendor status is ambiguous and needs confirmation.",
  },
  OVER_BILLED_VS_RECEIPT: {
    label: "Over-billed vs receipt",
    tone: "warning",
    help: "Invoice bills more than the received-but-unbilled quantity.",
  },
  SKU_ALIAS_UNRESOLVED: {
    label: "SKU alias unresolved",
    tone: "warning",
    help: "A vendor SKU matched only by description and needs confirmation.",
  },
  CURRENCY_MISMATCH: {
    label: "Currency mismatch",
    tone: "critical",
    help: "Invoice currency differs from the PO currency.",
  },
  DUPLICATE_INVOICE: {
    label: "Duplicate invoice",
    tone: "critical",
    help: "An invoice with these details was already processed.",
  },
  TAX_DISCREPANCY: {
    label: "Tax discrepancy",
    tone: "warning",
    help: "Tax total does not reconcile to the expected rate.",
  },
  INVOICE_QUALITY_WARN: {
    label: "Invoice quality warning",
    tone: "warning",
    help: "Some fields were read with low confidence.",
  },
  INVOICE_MISSING_FIELDS: {
    label: "Missing fields",
    tone: "warning",
    help: "Required invoice fields could not be read.",
  },
  SUPERVISOR_GUARDRAIL_VETO: {
    label: "Guardrail veto",
    tone: "critical",
    help: "A supervisor budget/cycle guardrail stopped the run.",
  },
  SPECIALIST_FAILED: {
    label: "Specialist failed",
    tone: "critical",
    help: "A specialist agent errored during the run.",
  },
};

export function blockingReasonMeta(code: string): BlockingReasonMeta {
  return (
    BLOCKING_REASON_META[code] ?? {
      label: code.replace(/_/g, " ").toLowerCase(),
      tone: "warning",
      help: "Unrecognized blocking reason — review manually.",
    }
  );
}

/** Tailwind class set per tone (Fluent semantic tints), shared by every badge. */
export const TONE_CLASSES: Record<Tone, string> = {
  neutral: "bg-surface-muted text-ink-secondary ring-stroke",
  positive: "bg-success-tint text-success ring-success/25",
  warning: "bg-warning-tint text-warning ring-warning/25",
  critical: "bg-danger-tint text-danger ring-danger/25",
};

/** Solid dot color per tone, for status indicators. */
export const TONE_DOT: Record<Tone, string> = {
  neutral: "bg-subtle",
  positive: "bg-success",
  warning: "bg-warning",
  critical: "bg-danger",
};
