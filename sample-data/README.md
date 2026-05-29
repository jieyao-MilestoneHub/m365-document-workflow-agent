# Sample data (synthetic)

All files here are **synthetic** and safe for a public repo — no real vendors, customers,
PII, or secrets (see `.claude/rules/hackathon.md`).

Two canonical invoices drive the demo and tests, both against PO-5000 / GRN-7000:

- **INV-1043** — clean: prices match the PO and quantities match the GRN → **pass**, balanced posting.
- **INV-1042** — line 1 is billed at 100.70 vs the PO's 95.00 (a +6% price variance, ≈$57 impact)
  → **hold** with `VARIANCE_OUTSIDE_TOLERANCE`, routed for review.
