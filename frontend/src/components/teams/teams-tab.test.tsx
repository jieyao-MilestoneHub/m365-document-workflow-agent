import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, it, vi, type Mock } from "vitest";

import { app } from "@microsoft/teams-js";
import { API_BASE } from "@/lib/env";
import { SCENARIOS } from "@/test/fixtures";
import { server } from "@/test/msw/server";

import { TeamsTab } from "./teams-tab";

vi.mock("@microsoft/teams-js", () => ({
  app: { initialize: vi.fn(), getContext: vi.fn() },
}));

describe("TeamsTab", () => {
  afterEach(() => vi.clearAllMocks());

  it("falls back to standalone when not hosted in Teams", async () => {
    (app.initialize as Mock).mockRejectedValue(new Error("no host"));
    server.use(http.get(`${API_BASE}/api/scenarios`, () => HttpResponse.json(SCENARIOS)));
    render(<TeamsTab />);
    expect(await screen.findByText("standalone")).toBeInTheDocument();
    // the inbox still renders standalone
    expect(await screen.findByText("INV-1042")).toBeInTheDocument();
  });

  it("reports the Teams host when initialization succeeds", async () => {
    (app.initialize as Mock).mockResolvedValue(undefined);
    (app.getContext as Mock).mockResolvedValue({ app: { theme: "default" } });
    server.use(http.get(`${API_BASE}/api/scenarios`, () => HttpResponse.json(SCENARIOS)));
    render(<TeamsTab />);
    expect(await screen.findByText("Teams host")).toBeInTheDocument();
  });
});
