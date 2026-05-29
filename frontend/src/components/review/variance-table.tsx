import { Badge } from "@/components/ui/badge";
import { ChartIcon } from "@/components/ui/icons";
import { Section } from "@/components/ui/section";
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
      <Section title="Variance evidence" icon={ChartIcon}>
        <p className="text-sm text-muted">No variance report available.</p>
      </Section>
    );
  }

  const overall = severityMeta(variance.overall_severity);
  return (
    <Section
      title="Variance evidence"
      icon={ChartIcon}
      aside={
        <div className="flex items-center gap-2 text-[11px] font-medium text-muted">
          <span>overall</span>
          <Badge tone={overall.tone} dot>
            {overall.label}
          </Badge>
          <span className="tabular-nums">
            {formatMoney(variance.financial_impact_total, currency)} impact
          </span>
        </div>
      }
      bodyClassName={variance.lines.length === 0 ? "p-4 sm:p-5" : "p-0"}
    >
      {variance.lines.length === 0 ? (
        <p className="flex items-center gap-2 text-sm text-success">
          <span className="h-1.5 w-1.5 rounded-full bg-success" />
          No line variances — all lines within tolerance.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b border-stroke bg-surface-alt text-[11px] uppercase tracking-wide text-subtle">
              <tr>
                <th className="px-4 py-2.5 font-semibold sm:px-5">Line</th>
                <th className="px-3 py-2.5 text-right font-semibold">Impact</th>
                <th className="px-3 py-2.5 font-semibold">Tolerance</th>
                <th className="px-3 py-2.5 font-semibold">Severity</th>
                <th className="px-4 py-2.5 font-semibold sm:px-5">Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stroke">
              {variance.lines.map((line) => {
                const sev = severityMeta(line.severity);
                return (
                  <tr key={line.invoice_line_no}>
                    <td className="px-4 py-3 tabular-nums text-muted sm:px-5">
                      {line.invoice_line_no}
                    </td>
                    <td className="px-3 py-3 text-right tabular-nums font-medium text-ink-secondary">
                      {formatMoney(line.financial_impact, currency)}
                    </td>
                    <td className="px-3 py-3">
                      <Badge tone={line.within_tolerance ? "positive" : "warning"}>
                        {line.within_tolerance ? "within" : "outside"}
                      </Badge>
                    </td>
                    <td className="px-3 py-3">
                      <Badge tone={sev.tone} dot>
                        {sev.label}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-ink-secondary sm:px-5">
                      {line.rationale ?? "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </Section>
  );
}
