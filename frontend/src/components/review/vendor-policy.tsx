import { BuildingIcon } from "@/components/ui/icons";
import { Section } from "@/components/ui/section";
import { formatMoney } from "@/lib/format";
import type { JobDetail } from "@/lib/types";

function Field({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="min-w-0">
      <dt className="text-[11px] font-semibold uppercase tracking-wide text-subtle">{label}</dt>
      <dd className={`truncate text-sm text-ink ${mono ? "font-mono" : ""}`}>{value}</dd>
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
    <Section title="Vendor & policy" icon={BuildingIcon}>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-4">
        <Field label="Vendor" value={inv?.vendor_name ?? "—"} />
        <Field label="Vendor ID" value={inv?.vendor_id ?? "—"} mono />
        <Field label="Currency" value={currency} />
        <Field label="Invoice total" value={formatMoney(inv?.total, currency)} />
        <Field label="PO ref" value={inv?.po_ref ?? job.match?.po_number ?? "—"} mono />
        <Field label="GRN ref" value={inv?.grn_ref ?? job.match?.grn_number ?? "—"} mono />
      </dl>

      <div className="mt-4 border-t border-stroke pt-4">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-subtle">
          Policy versions in effect
        </p>
        <dl className="mt-2.5 grid grid-cols-3 gap-x-4 gap-y-3">
          <Field label="Tolerance" value={job.match?.tolerance_version ?? "—"} mono />
          <Field label="Thresholds" value={job.variance?.thresholds_version ?? "—"} mono />
          <Field label="GL map" value={job.posting?.gl_map_version ?? "—"} mono />
        </dl>
      </div>
    </Section>
  );
}
