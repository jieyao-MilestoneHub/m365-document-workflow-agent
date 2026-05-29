import { Badge } from "@/components/ui/badge";
import { ScaleIcon } from "@/components/ui/icons";
import { Section } from "@/components/ui/section";
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
      <Section title="Three-way match" icon={ScaleIcon}>
        <p className="text-sm text-muted">No match report available for this job.</p>
      </Section>
    );
  }

  const matchByLine = new Map(match.lines.map((l) => [l.invoice_line_no, l]));
  const invoiceLines = invoice?.line_items ?? [];
  const currency = invoice?.currency ?? match.po_currency ?? "USD";

  return (
    <Section
      title="Three-way match"
      icon={ScaleIcon}
      aside={
        <div className="flex flex-wrap items-center gap-2 text-[11px] font-medium text-muted">
          {match.po_number ? (
            <span className="rounded bg-surface-muted px-1.5 py-0.5 font-mono ring-1 ring-inset ring-stroke">
              PO {match.po_number}
            </span>
          ) : null}
          {match.grn_number ? (
            <span className="rounded bg-surface-muted px-1.5 py-0.5 font-mono ring-1 ring-inset ring-stroke">
              GRN {match.grn_number}
            </span>
          ) : null}
          {match.currency_mismatch ? <Badge tone="critical">Currency mismatch</Badge> : null}
        </div>
      }
      bodyClassName="p-0"
    >
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="border-b border-stroke bg-surface-alt text-[11px] uppercase tracking-wide text-subtle">
            <tr>
              <th className="px-4 py-2.5 font-semibold sm:px-5">Line</th>
              <th className="px-3 py-2.5 font-semibold">Description</th>
              <th className="px-3 py-2.5 text-right font-semibold">Invoice qty × price</th>
              <th className="px-3 py-2.5 text-right font-semibold">PO price</th>
              <th className="px-3 py-2.5 text-right font-semibold">GRN recv</th>
              <th className="px-3 py-2.5 text-right font-semibold">Δ price</th>
              <th className="px-3 py-2.5 text-right font-semibold">Variance</th>
              <th className="px-4 py-2.5 font-semibold sm:px-5">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-stroke">
            {invoiceLines.map((line) => {
              const m = matchByLine.get(line.line_no);
              const status = m ? lineStatusMeta(m.status) : null;
              const pct = m ? variancePercent(m) : null;
              const flagged = m ? !m.within_tolerance || m.over_billed : false;
              return (
                <tr key={line.line_no} className={flagged ? "bg-warning-tint/45" : undefined}>
                  <td className="px-4 py-3 tabular-nums text-muted sm:px-5">{line.line_no}</td>
                  <td className="px-3 py-3 text-ink-secondary">
                    {line.description}
                    {m?.resolved_sku ? (
                      <span className="ml-1.5 font-mono text-[11px] text-subtle">
                        {m.resolved_sku}
                      </span>
                    ) : null}
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums text-ink-secondary">
                    {formatQuantity(line.quantity)} × {formatMoney(line.unit_price, currency)}
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums text-ink-secondary">
                    {formatMoney(m?.po_unit_price, currency)}
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums text-ink-secondary">
                    {formatQuantity(m?.received_quantity)}
                  </td>
                  <td
                    className={`px-3 py-3 text-right tabular-nums ${flagged ? "font-semibold text-warning" : "text-ink-secondary"}`}
                  >
                    {m ? formatSignedNumber(m.price_delta) : "—"}
                  </td>
                  <td className="px-3 py-3 text-right">
                    {pct ? (
                      <Badge tone={flagged ? "warning" : "neutral"}>{pct}</Badge>
                    ) : (
                      <span className="text-subtle">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 sm:px-5">
                    {status ? (
                      <Badge tone={status.tone} dot>
                        {status.label}
                      </Badge>
                    ) : (
                      <span className="text-xs text-subtle">no match</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {match.citations.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 border-t border-stroke px-4 py-3 sm:px-5">
          <span className="text-xs font-medium text-muted">Evidence</span>
          {match.citations.map((c, i) => (
            <CitedText key={`${c.document_id}-${i}`} citation={c} />
          ))}
        </div>
      )}
    </Section>
  );
}
