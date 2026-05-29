import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { HumanDecision } from "@/lib/types";

import { DecisionPanel } from "./decision-panel";

describe("DecisionPanel", () => {
  it("requires a reviewer name before posting", async () => {
    const onDecide = vi.fn().mockResolvedValue(undefined);
    render(<DecisionPanel humanDecision={null} onDecide={onDecide} />);
    await userEvent.click(screen.getByRole("button", { name: "Approve" }));
    expect(onDecide).not.toHaveBeenCalled();
    expect(screen.getByText(/Enter your name/)).toBeInTheDocument();
  });

  it("posts an approve decision with reviewer + note", async () => {
    const onDecide = vi.fn().mockResolvedValue(undefined);
    render(<DecisionPanel humanDecision={null} onDecide={onDecide} />);
    await userEvent.type(screen.getByLabelText("Reviewer name"), "Jane");
    await userEvent.type(screen.getByLabelText("Decision note"), "renegotiated");
    await userEvent.click(screen.getByRole("button", { name: "Approve" }));
    expect(onDecide).toHaveBeenCalledWith({
      action: "approve",
      reviewer: "Jane",
      note: "renegotiated",
    });
  });

  it("reflects an existing human decision instead of the form", () => {
    const decision: HumanDecision = {
      action: "reject",
      reviewer: "Sam",
      note: "credit requested",
      ts: "2026-05-29T09:00:00Z",
    };
    render(<DecisionPanel humanDecision={decision} onDecide={vi.fn()} />);
    expect(screen.getByText("Rejected")).toBeInTheDocument();
    expect(screen.getByText(/by Sam/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Approve" })).not.toBeInTheDocument();
  });
});
