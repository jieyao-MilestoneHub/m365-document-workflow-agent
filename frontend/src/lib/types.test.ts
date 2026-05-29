import { describe, expect, it } from "vitest";

import { JOB_HOLD, JOB_PASS, SCENARIOS } from "@/test/fixtures";

import { JobDetailSchema, ScenarioInfoSchema } from "./types";
import { z } from "zod";

describe("contract schemas", () => {
  it("accept the canonical fixtures (contract drift guard)", () => {
    expect(() => z.array(ScenarioInfoSchema).parse(SCENARIOS)).not.toThrow();
    expect(() => JobDetailSchema.parse(JOB_HOLD)).not.toThrow();
    expect(() => JobDetailSchema.parse(JOB_PASS)).not.toThrow();
  });

  it("reject an unknown decision value", () => {
    expect(() => JobDetailSchema.parse({ ...JOB_HOLD, decision: "maybe" })).toThrow();
  });

  it("keep money fields as strings (exact display)", () => {
    const job = JobDetailSchema.parse(JOB_HOLD);
    expect(job.invoice?.total).toBe("10918.00");
    expect(typeof job.posting?.lines[0].amount).toBe("string");
  });
});
