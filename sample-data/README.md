# Sample data (synthetic)

All files here are **synthetic** and safe for a public repo — no real vendors, customers,
PII, or secrets (see `.claude/rules/hackathon.md`). Synthetic-by-design is the *correct*
posture: AP data is confidential, and a curated edge-case corpus lets us *deterministically
prove* behaviour on the exceptions that matter. This catalog is both the test suite
(`backend/tests/test_scenarios.py`) and the demo script.

Two vendor personas: **Globex** (clean) and **Contoso** (hold-listed). Run any scenario with
`python -m app.cli <ID>` from `backend/`.

| ID | Scenario | Expected |
|----|----------|----------|
| INV-1043 | clean three-way match | **PASS** |
| INV-1050 | partial receipt (6 of 10), billed within tolerance | **PASS** |
| INV-1051 | vendor SKU `GLX-WA-01` resolves to `WIDGET-A` via alias | **PASS** |
| INV-1042 | unit price 100.70 vs PO 95.00 (+6%, ≈$57 impact) | **HOLD** · VARIANCE_OUTSIDE_TOLERANCE |
| INV-1052 | invoice tax 35.50 vs expected 47.50 | **HOLD** · TAX_DISCREPANCY |
| INV-1053 | 10 received but 8 already invoiced; bills 10 (only 2 billable) | **HOLD** · OVER_BILLED_VS_RECEIPT |
| INV-1054 | unit price 150 vs PO 95 (≥$500 impact) | **ESCALATE** · VARIANCE_HIGH_SEVERITY |
| INV-1055 | invoice in EUR, PO in USD | **ESCALATE** · CURRENCY_MISMATCH |
| INV-1056 | invoice number already in the posted ledger | **ESCALATE** · DUPLICATE_INVOICE |
| INV-1057 | `po_ref` unreadable → agent asks → human supplies PO-5000 | **HOLD → PASS** (slot-fill) |
| INV-1058 | vendor `Contoso` is on the hold list | **HOLD** · VENDOR_ON_HOLD_LIST |
| INV-1059 | $75 freight charge line above the $25 freight tolerance | **HOLD** · UNPLANNED_CHARGE |
| INV-1060 | WIDGET-A billed in `case` vs PO `ea`, no conversion factor | **ESCALATE** · UOM_MISMATCH |

Demo arc: INV-1043 → **INV-1042** (the +6% money shot) → INV-1053 (line-level depth) →
INV-1054 (guardrail overrides the LLM) → INV-1057 (human clears it) → INV-1056 (control catch).

Reference data: `purchase_orders/`, `goods_receipts/`, `policy.json` (tolerance, thresholds,
GL map incl. freight account, freight tolerance, vendor lists, SKU aliases),
`invoiced_to_date.json` (billing history),
`posted_ledger.json` (duplicate control), `human_answers.json` (scripted slot-fill answers).
