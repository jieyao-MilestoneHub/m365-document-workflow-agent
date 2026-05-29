import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { SCENARIOS } from "@/test/fixtures";
import { server } from "@/test/msw/server";

import { api, ApiError } from "./api";
import { API_BASE } from "./env";

describe("api boundary", () => {
  it("zod-parses the scenarios list", async () => {
    server.use(http.get(`${API_BASE}/api/scenarios`, () => HttpResponse.json(SCENARIOS)));
    const result = await api.scenarios();
    expect(result).toHaveLength(2);
    expect(result[0]).toMatchObject({ id: "INV-1042", vendor: "Northwind Supplies" });
  });

  it("rejects a malformed response (security: never render unvalidated data)", async () => {
    server.use(http.get(`${API_BASE}/api/scenarios`, () => HttpResponse.json([{ id: 5 }])));
    await expect(api.scenarios()).rejects.toThrow();
  });

  it("wraps non-2xx responses in ApiError with the status", async () => {
    server.use(
      http.post(`${API_BASE}/api/jobs`, () => HttpResponse.json({ detail: "nope" }, { status: 404 })),
    );
    await expect(api.createJob("INV-9999")).rejects.toBeInstanceOf(ApiError);
  });
});
