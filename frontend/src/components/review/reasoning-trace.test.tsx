import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { JOB_HOLD } from "@/test/fixtures";
import { installMockEventSource, MockEventSource } from "@/test/mock-eventsource";

import { AgentReasoningTrace } from "./reasoning-trace";

describe("AgentReasoningTrace", () => {
  beforeEach(() => installMockEventSource());
  afterEach(() => vi.unstubAllGlobals());

  it("renders streamed trace events then marks the stream complete", () => {
    render(<AgentReasoningTrace jobId="job1042abcd" />);
    expect(screen.getByText(/Waiting for the agent/)).toBeInTheDocument();

    const source = MockEventSource.last;
    act(() => {
      JOB_HOLD.events.forEach((e) => source.emit("trace", e));
    });
    expect(screen.getByText("line 2 price variance vs PO-5001")).toBeInTheDocument();
    expect(screen.getAllByText("delegate_result")).toHaveLength(2);

    act(() => {
      source.emit("completed", {
        job_id: "job1042abcd",
        decision: "hold",
        summary: "held",
        blocking_reasons: ["VARIANCE_OUTSIDE_TOLERANCE"],
      });
    });
    expect(screen.getByText("complete")).toBeInTheDocument();
  });

  it("surfaces a stream error", () => {
    render(<AgentReasoningTrace jobId="job1042abcd" />);
    act(() => MockEventSource.last.emitError());
    expect(screen.getByText("stream error")).toBeInTheDocument();
  });
});
