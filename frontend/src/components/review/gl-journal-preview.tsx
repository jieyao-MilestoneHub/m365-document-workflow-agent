import { Badge } from "@/components/ui/badge";
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
      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h3 className="text-sm font-semibold text-slate-800">GL journal preview</h3>
        <p className="mt-2 text-sm text-slate-500">No posting draft available.</p>
      </section>
    );
  }

  const currency = posting.currency || "USD";
  const debitTotal = sum(posting.lines.filter((l) => l.direction === "debit").map((l) => l.amount));
  const creditTotal = sum(
    posting.lines.filter((l) => l.direction === "credit").map((l) => l.amount),
  );

  return (
    <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-800">GL journal preview</h3>
        <Badge tone={posting.balanced ? "positive" : "critical"}>
          {posting.balanced ? "Balanced" : "Unbalanced"}
        </Badge>
      </div>

      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-2 py-2 font-medium">Account</th>
            <th className="px-2 py-2 font-medium">Memo</th>
            <th className="px-2 py-2 text-right font-medium">Debit</th>
            <th className="px-2 py-2 text-right font-medium">Credit</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {posting.lines.map((line, i) => (
            <tr key={`${line.gl_account}-${i}`}>
              <td className="px-2 py-2 font-mono text-slate-700">{line.gl_account}</td>
              <td className="px-2 py-2 text-slate-600">{line.memo ?? "—"}</td>
              <td className="px-2 py-2 text-right tabular-nums text-slate-700">
                {line.direction === "debit" ? formatMoney(line.amount, currency) : ""}
              </td>
              <td className="px-2 py-2 text-right tabular-nums text-slate-700">
                {line.direction === "credit" ? formatMoney(line.amount, currency) : ""}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot className="border-t border-slate-200 text-sm font-medium">
          <tr>
            <td className="px-2 py-2" colSpan={2}>
              Totals
            </td>
            <td className="px-2 py-2 text-right tabular-nums">
              {formatMoney(String(debitTotal), currency)}
            </td>
            <td className="px-2 py-2 text-right tabular-nums">
              {formatMoney(String(creditTotal), currency)}
            </td>
          </tr>
        </tfoot>
      </table>

      {posting.notes.length > 0 && (
        <ul className="list-disc space-y-1 pl-5 text-xs text-slate-500">
          {posting.notes.map((note, i) => (
            <li key={i}>{note}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
