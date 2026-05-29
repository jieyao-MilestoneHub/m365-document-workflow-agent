import { formatMoney } from "@/lib/format";
import type { JobDetail } from "@/lib/types";

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="text-sm text-slate-700">{value}</dd>
    </div>
  );
}

/**
 * Read-only vendor identity + the policy versions in effect for this job. There is no policy
 * endpoint yet, so this is derived from the job's own data (invoice / match / variance /
 * posting), which carry the active rule versions.
 */
export function VendorPolicyPanel({ job }: { job: JobDetail }) {
  const inv = job.invoice;
  const currency = inv?.currency ?? "USD";
  return (
    <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="text-sm font-semibold text-slate-800">Vendor &amp; policy</h3>

      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <Field label="Vendor" value={inv?.vendor_name ?? "—"} />
        <Field label="Vendor ID" value={inv?.vendor_id ?? "—"} />
        <Field label="Currency" value={currency} />
        <Field label="PO ref" value={inv?.po_ref ?? job.match?.po_number ?? "—"} />
        <Field label="GRN ref" value={inv?.grn_ref ?? job.match?.grn_number ?? "—"} />
        <Field label="Invoice total" value={formatMoney(inv?.total, currency)} />
      </dl>

      <div className="border-t border-slate-100 pt-3">
        <p className="text-xs uppercase tracking-wide text-slate-400">Policy versions in effect</p>
        <dl className="mt-2 grid grid-cols-2 gap-4 sm:grid-cols-3">
          <Field label="Tolerance" value={job.match?.tolerance_version ?? "—"} />
          <Field label="Thresholds" value={job.variance?.thresholds_version ?? "—"} />
          <Field label="GL map" value={job.posting?.gl_map_version ?? "—"} />
        </dl>
      </div>
    </section>
  );
}
