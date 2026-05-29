import { Badge } from "@/components/ui/badge";
import { LedgerIcon } from "@/components/ui/icons";
import { Section } from "@/components/ui/section";
import { formatMoney } from "@/lib/format";
import type { PostingDraft } from "@/lib/types";

function sum(values: string[]): number {
  return values.reduce((acc, v) => acc + (Number(v) || 0), 0);
}

/**
 * GL journal draft: debit/credit lines with totals and a balance check. The balance is
 * recomputed from the lines for display, alongside the backend's authoritative `balanced`
 * flag — a variance never auto-posts, so this is a preview only.
 */
export function GLJournalPreview({ posting }: { posting: PostingDraft | null }) {
  if (!posting) {
    return (
      <Section title="GL journal preview" icon={LedgerIcon}>
        <p className="text-sm text-muted">No posting draft available.</p>
      </Section>
    );
  }

  const currency = posting.currency || "USD";
  const debitTotal = sum(posting.lines.filter((l) => l.direction === "debit").map((l) => l.amount));
  const creditTotal = sum(
    posting.lines.filter((l) => l.direction === "credit").map((l) => l.amount),
  );

  return (
    <Section
      title="GL journal preview"
      icon={LedgerIcon}
      aside={
        <Badge tone={posting.balanced ? "positive" : "critical"} dot>
          {posting.balanced ? "Balanced" : "Unbalanced"}
        </Badge>
      }
      bodyClassName="p-0"
    >
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead className="border-b border-stroke bg-surface-alt text-[11px] uppercase tracking-wide text-subtle">
            <tr>
              <th className="px-4 py-2.5 font-semibold sm:px-5">Account</th>
              <th className="px-3 py-2.5 font-semibold">Memo</th>
              <th className="px-3 py-2.5 text-right font-semibold">Debit</th>
              <th className="px-4 py-2.5 text-right font-semibold sm:px-5">Credit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-stroke">
            {posting.lines.map((line, i) => (
              <tr key={`${line.gl_account}-${i}`}>
                <td className="px-4 py-3 font-mono text-ink sm:px-5">{line.gl_account}</td>
                <td className="px-3 py-3 text-ink-secondary">{line.memo ?? "—"}</td>
                <td className="px-3 py-3 text-right tabular-nums text-ink-secondary">
                  {line.direction === "debit" ? formatMoney(line.amount, currency) : ""}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-ink-secondary sm:px-5">
                  {line.direction === "credit" ? formatMoney(line.amount, currency) : ""}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot className="border-t-2 border-stroke-strong bg-surface-alt text-sm font-semibold text-ink">
            <tr>
              <td className="px-4 py-3 sm:px-5" colSpan={2}>
                Totals
              </td>
              <td className="px-3 py-3 text-right tabular-nums">
                {formatMoney(String(debitTotal), currency)}
              </td>
              <td className="px-4 py-3 text-right tabular-nums sm:px-5">
                {formatMoney(String(creditTotal), currency)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {posting.notes.length > 0 && (
        <ul className="list-disc space-y-1 border-t border-stroke px-8 py-3 text-xs text-muted">
          {posting.notes.map((note, i) => (
            <li key={i}>{note}</li>
          ))}
        </ul>
      )}
    </Section>
  );
}
