import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { API_BASE } from "@/lib/env";
import { JOB_HOLD, SCENARIOS } from "@/test/fixtures";
import { server } from "@/test/msw/server";

import { InboxTable } from "./inbox-table";

describe("InboxTable", () => {
  it("renders the scenario rows from the API", async () => {
    server.use(http.get(`${API_BASE}/api/scenarios`, () => HttpResponse.json(SCENARIOS)));
    render(<InboxTable />);
    expect(await screen.findByText("INV-1042")).toBeInTheDocument();
    expect(screen.getByText("INV-1043")).toBeInTheDocument();
    expect(screen.getAllByText("Northwind Supplies")).toHaveLength(2);
  });

  it("processes an invoice and shows the decision badge + a review link", async () => {
    server.use(
      http.get(`${API_BASE}/api/scenarios`, () => HttpResponse.json(SCENARIOS)),
      http.post(`${API_BASE}/api/jobs`, () => HttpResponse.json(JOB_HOLD)),
    );
    render(<InboxTable />);
    await screen.findByText("INV-1042");

    const rows = screen.getAllByRole("row");
    const inv1042Row = rows.find((r) => r.textContent?.includes("INV-1042"))!;
    await userEvent.click(within(inv1042Row).getByRole("button", { name: "Process" }));

    await waitFor(() => expect(within(inv1042Row).getByText("Hold")).toBeInTheDocument());
    const link = within(inv1042Row).getByRole("link", { name: "Review" });
    expect(link).toHaveAttribute("href", `/review/${JOB_HOLD.job_id}`);
  });

  it("shows an error state when the API is unreachable", async () => {
    server.use(http.get(`${API_BASE}/api/scenarios`, () => HttpResponse.error()));
    render(<InboxTable />);
    expect(await screen.findByText(/Could not load invoices/i)).toBeInTheDocument();
  });
});
