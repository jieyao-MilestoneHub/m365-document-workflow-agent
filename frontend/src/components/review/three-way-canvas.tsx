import { Badge } from "@/components/ui/badge";
import { formatMoney, formatQuantity, formatSignedNumber } from "@/lib/format";
import { lineStatusMeta } from "@/lib/registry";
import type { LineMatch, ThreeWayMatchReport, VendorInvoice } from "@/lib/types";

import { CitedText } from "./cited-text";

function variancePercent(line: LineMatch): string | null {
  if (line.po_unit_price == null) return null;
  const po = Number(line.po_unit_price);
  const delta = Number(line.price_delta);
  if (!po || Number.isNaN(po) || Number.isNaN(delta)) return null;
  const pct = (delta / po) * 100;
  return `${pct > 0 ? "+" : ""}${pct.toFixed(1)}%`;
}

/** PO ↔ GRN ↔ Invoice comparison: per-line invoice vs PO price vs GRN receipt, with deltas. */
export function ThreeWayMatchCanvas({
  invoice,
  match,
}: {
  invoice: VendorInvoice | null;
  match: ThreeWayMatchReport | null;
}) {
  if (!match) {
    return (
      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h3 className="text-sm font-semibold text-slate-800">Three-way match</h3>
        <p className="mt-2 text-sm text-slate-500">No match report available for this job.</p>
      </section>
    );
  }

  const matchByLine = new Map(match.lines.map((l) => [l.invoice_line_no, l]));
  const invoiceLines = invoice?.line_items ?? [];
  const currency = invoice?.currency ?? match.po_currency ?? "USD";

  return (
    <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-800">Three-way match</h3>
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
          {match.po_number ? <span className="font-mono">PO {match.po_number}</span> : null}
          {match.grn_number ? <span className="font-mono">GRN {match.grn_number}</span> : null}
          {match.currency_mismatch ? <Badge tone="critical">Currency mismatch</Badge> : null}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-2 py-2 font-medium">Line</th>
              <th className="px-2 py-2 font-medium">Description</th>
              <th className="px-2 py-2 text-right font-medium">Invoice qty × price</th>
              <th className="px-2 py-2 text-right font-medium">PO price</th>
              <th className="px-2 py-2 text-right font-medium">GRN recv</th>
              <th className="px-2 py-2 text-right font-medium">Δ price</th>
              <th className="px-2 py-2 text-right font-medium">Variance</th>
              <th className="px-2 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {invoiceLines.map((line) => {
              const m = matchByLine.get(line.line_no);
              const status = m ? lineStatusMeta(m.status) : null;
              const pct = m ? variancePercent(m) : null;
              const flagged = m ? !m.within_tolerance || m.over_billed : false;
              return (
                <tr key={line.line_no} className={flagged ? "bg-amber-50/60" : undefined}>
                  <td className="px-2 py-2 tabular-nums text-slate-600">{line.line_no}</td>
                  <td className="px-2 py-2 text-slate-700">
                    {line.description}
                    {m?.resolved_sku ? (
                      <span className="ml-1 font-mono text-xs text-slate-400">{m.resolved_sku}</span>
                    ) : null}
                  </td>
                  <td className="px-2 py-2 text-right tabular-nums text-slate-700">
                    {formatQuantity(line.quantity)} × {formatMoney(line.unit_price, currency)}
                  </td>
                  <td className="px-2 py-2 text-right tabular-nums text-slate-700">
                    {formatMoney(m?.po_unit_price, currency)}
                  </td>
                  <td className="px-2 py-2 text-right tabular-nums text-slate-700">
                    {formatQuantity(m?.received_quantity)}
                  </td>
                  <td className="px-2 py-2 text-right tabular-nums text-slate-700">
                    {m ? formatSignedNumber(m.price_delta) : "—"}
                  </td>
                  <td className="px-2 py-2 text-right">
                    {pct ? (
                      <Badge tone={flagged ? "warning" : "neutral"}>{pct}</Badge>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="px-2 py-2">
                    {status ? (
                      <Badge tone={status.tone}>{status.label}</Badge>
                    ) : (
                      <span className="text-xs text-slate-400">no match</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {match.citations.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-xs text-slate-500">Evidence:</span>
          {match.citations.map((c, i) => (
            <CitedText key={`${c.document_id}-${i}`} citation={c} />
          ))}
        </div>
      )}
    </section>
  );
}
