import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { JOB_HOLD } from "@/test/fixtures";

import { GLJournalPreview } from "./gl-journal-preview";

describe("GLJournalPreview", () => {
  it("shows the balanced badge and the GL lines", () => {
    render(<GLJournalPreview posting={JOB_HOLD.posting} />);
    expect(screen.getByText("Balanced")).toBeInTheDocument();
    expect(screen.getByText("2100")).toBeInTheDocument();
    // unique expense debit line
    expect(screen.getByText("$10,300.00")).toBeInTheDocument();
  });

  it("renders an unbalanced badge when the draft does not balance", () => {
    render(
      <GLJournalPreview
        posting={{ ...JOB_HOLD.posting!, balanced: false }}
      />,
    );
    expect(screen.getByText("Unbalanced")).toBeInTheDocument();
  });
});
