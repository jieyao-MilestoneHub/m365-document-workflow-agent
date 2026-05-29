import { render, screen, within } from "@testing-library/react";
import { formatMoney } from "@/lib/format";
import { describe, expect, it } from "vitest";

import { JOB_HOLD } from "@/test/fixtures";

import { AuditTrail } from "./audit-trail";
import { VendorPolicyPanel } from "./vendor-policy";

describe("AuditTrail", () => {
  it("lists each handoff with roles and reason code", () => {
    render(<AuditTrail history={JOB_HOLD.handoff_history} />);
    const rows = screen.getAllByRole("row").slice(1); // drop header
    expect(rows).toHaveLength(JOB_HOLD.handoff_history.length);
    const matcherRow = rows.find((r) => r.textContent?.includes("po_grn_matcher"))!;
    expect(within(matcherRow).getByText("delegate")).toBeInTheDocument();
  });

  it("renders an empty state with no handoffs", () => {
    render(<AuditTrail history={[]} />);
    expect(screen.getByText("No handoffs recorded.")).toBeInTheDocument();
  });
});

describe("VendorPolicyPanel", () => {
  it("shows vendor identity and the active policy versions from the job", () => {
    render(<VendorPolicyPanel job={JOB_HOLD} />);
    expect(screen.getByText("Northwind Supplies")).toBeInTheDocument();
    expect(screen.getByText("PO-5001")).toBeInTheDocument();
    expect(screen.getByText(formatMoney("10918.00", "USD"))).toBeInTheDocument();
    // tolerance + thresholds versions both render
    expect(screen.getAllByText("2026.04.1")).toHaveLength(2);
  });
});
