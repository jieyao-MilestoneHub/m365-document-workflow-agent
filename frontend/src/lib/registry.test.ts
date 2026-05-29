import { describe, expect, it } from "vitest";

import { blockingReasonMeta, decisionMeta, severityMeta } from "./registry";

describe("presentation registries (OCP)", () => {
  it("maps known codes to display metadata", () => {
    expect(decisionMeta("hold").tone).toBe("warning");
    expect(blockingReasonMeta("VARIANCE_OUTSIDE_TOLERANCE").label).toBe("Variance outside tolerance");
    expect(severityMeta("high").tone).toBe("critical");
  });

  it("falls back safely for an unknown blocking reason (new backend code renders)", () => {
    const meta = blockingReasonMeta("SOME_FUTURE_REASON");
    expect(meta.label).toBe("some future reason");
    expect(meta.tone).toBe("warning");
  });

  it("falls back for an unknown decision without throwing", () => {
    expect(decisionMeta("weird")).toMatchObject({ label: "weird", tone: "neutral" });
  });
});
