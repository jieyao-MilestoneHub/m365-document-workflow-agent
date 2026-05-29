import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { JOB_HOLD } from "@/test/fixtures";

import { ThreeWayMatchCanvas } from "./three-way-canvas";

describe("ThreeWayMatchCanvas", () => {
  it("flags the out-of-tolerance line with a variance % and status badge", () => {
    render(<ThreeWayMatchCanvas invoice={JOB_HOLD.invoice} match={JOB_HOLD.match} />);
    const rows = screen.getAllByRole("row");
    const line2 = rows.find((r) => r.textContent?.includes("Hex bolt pack"))!;
    // price_delta 3.00 on po_unit_price 50.00 → +6.0%
    expect(within(line2).getByText("+6.0%")).toBeInTheDocument();
    expect(within(line2).getByText("Price variance")).toBeInTheDocument();
  });

  it("reveals the cited PO snippet on click (plain text, no HTML injection)", async () => {
    render(<ThreeWayMatchCanvas invoice={JOB_HOLD.invoice} match={JOB_HOLD.match} />);
    await userEvent.click(screen.getByRole("button", { name: /Purchase Order PO-5001/ }));
    expect(screen.getByRole("tooltip")).toHaveTextContent(
      "Line 2 — Hex bolt pack — unit price 50.00 USD",
    );
  });
});
