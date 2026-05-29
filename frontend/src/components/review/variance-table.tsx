import { Badge } from "@/components/ui/badge";
import { formatMoney } from "@/lib/format";
import { severityMeta } from "@/lib/registry";
import type { VarianceReport } from "@/lib/types";

/** Per-line financial impact, tolerance and severity with the assessor's rationale. */
export function VarianceEvidenceTable({
  variance,
  currency = "USD",
}: {
  variance: VarianceReport | null;
  currency?: string;
}) {
  if (!variance) {
    return (
      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h3 className="text-sm font-semibold text-slate-800">Variance evidence</h3>
        <p className="mt-2 text-sm text-slate-500">No variance report available.</p>
      </section>
    );
  }

  const overall = severityMeta(variance.overall_severity);
  return (
    <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-800">Variance evidence</h3>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span>overall</span>
          <Badge tone={overall.tone}>{overall.label}</Badge>
          <span className="tabular-nums">
            {formatMoney(variance.financial_impact_total, currency)} total impact
          </span>
        </div>
      </div>

      {variance.lines.length === 0 ? (
        <p className="text-sm text-emerald-700">No line variances — all lines within tolerance.</p>
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-2 py-2 font-medium">Line</th>
              <th className="px-2 py-2 text-right font-medium">Impact</th>
              <th className="px-2 py-2 font-medium">Tolerance</th>
              <th className="px-2 py-2 font-medium">Severity</th>
              <th className="px-2 py-2 font-medium">Rationale</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {variance.lines.map((line) => {
              const sev = severityMeta(line.severity);
              return (
                <tr key={line.invoice_line_no}>
                  <td className="px-2 py-2 tabular-nums text-slate-600">{line.invoice_line_no}</td>
                  <td className="px-2 py-2 text-right tabular-nums text-slate-700">
                    {formatMoney(line.financial_impact, currency)}
                  </td>
                  <td className="px-2 py-2">
                    <Badge tone={line.within_tolerance ? "positive" : "warning"}>
                      {line.within_tolerance ? "within" : "outside"}
                    </Badge>
                  </td>
                  <td className="px-2 py-2">
                    <Badge tone={sev.tone}>{sev.label}</Badge>
                  </td>
                  <td className="px-2 py-2 text-slate-600">{line.rationale ?? "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}
