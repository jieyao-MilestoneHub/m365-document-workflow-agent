# Sample data (synthetic)

All files here are **synthetic** and safe for a public repo — no real vendors, customers,
PII, or secrets (see `.claude/rules/hackathon.md`). Synthetic-by-design is the *correct*
posture: AP data is confidential, and a curated edge-case corpus lets us *deterministically
prove* behaviour on the exceptions that matter. This catalog is both the test suite
(`backend/tests/test_scenarios.py`, driven by `expected_results.json`) and the demo script.

Run the interactive triage with `python -m app.cli triage`, or any single scenario with
`python -m app.cli <ID>` from `backend/`.

## Retail deduction-control scenarios (the demo)

Retail vendor personas: **Northwind Beverages** and **Fabrikam Foods**. Beverages are billed by
the **case**; the PO/GRN base unit varies (case or each), which is exactly where UOM mismatches
hide.

| ID | Scenario | Expected |
|----|----------|----------|
| INV-1001 | clean three-way match (300 cases water @ $8.00) | **PASS** · payable $2,400 |
| INV-1002 | short receipt: billed 500 cases @ $6.00, GRN accepted 420 | **HOLD** · `OVER_BILLED_VS_RECEIPT` (+ `VARIANCE_OUTSIDE_TOLERANCE`) · pay $2,520 / **hold $480** |
| **INV-1003** | qty + price match the PO/GRN exactly, but PROMO-MAY-BEV's **$3/case allowance is missing** (8,400 cases) | **HOLD** · `PROMOTION_ALLOWANCE_MISSING` · **margin leakage $25,200** · pay $126,000 / hold $25,200 · route category_manager |
| INV-1004 | 100 cases @ $18.00 with `uom_factor` 24; PO is 2,400 **each** @ $0.75 — normalizes | **PASS** (false hold avoided) |
| INV-1005 | same shape as INV-1004 but **no** conversion factor (case vs each) | **ESCALATE** · `UOM_MISMATCH` (to master data) |
| INV-1006 | PROMO-MAY-BEV applies and the invoice **carries the matching $25,200 allowance** | **PASS** (no false positive) |

Demo arc (interactive investigation): `triage` the batch → drill into **INV-1003** ("it passed
three-way match — why hold it?") → the agent explains the missing allowance and the $25,200
leakage → "show me the evidence" → PO / GRN / invoice lines + the **PROMO-MAY-BEV** citation.

Retail reference data:
- `promotions.json` — trade-promotion agreements (vendor, SKU, `allowance_per_unit`, effective
  window, routing). The `KnowledgePort` (Foundry IQ in prod) grounds these with citations.
- `expected_results.json` — per-invoice expected decision, blocking reasons, margin leakage, and
  pay-now / hold split. The contract the engine (and later the Azure adapters) must reproduce.

## Legacy AP regression scenarios (not in the demo)

Retained so the original deterministic-core behaviour stays locked while the retail layer is
added. Two personas: **Globex** (clean) and **Contoso** (hold-listed).

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

Shared reference data: `purchase_orders/`, `goods_receipts/`, `policy.json` (tolerance,
thresholds, GL map incl. freight account, freight tolerance, **allowance tolerance**, vendor
lists, SKU aliases), `invoiced_to_date.json` (billing history), `posted_ledger.json` (duplicate
control), `human_answers.json` (scripted slot-fill answers).
</content>
