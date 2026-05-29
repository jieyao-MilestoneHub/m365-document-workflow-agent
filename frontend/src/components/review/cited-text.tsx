"use client";

import { useState } from "react";

import { QuoteIcon } from "@/components/ui/icons";
import type { Citation } from "@/lib/types";

/**
 * Foundry IQ citation flyout. Shows the source document title and the exact cited snippet
 * on click. Everything is rendered as plain text children — never dangerouslySetInnerHTML —
 * so an attacker-controlled snippet cannot inject markup.
 */
export function CitedText({ citation }: { citation: Citation }) {
  const [open, setOpen] = useState(false);
  return (
    <span className="relative inline-block">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="inline-flex items-center gap-1.5 rounded-md bg-brand-tint px-2.5 py-1 text-xs font-semibold text-brand-ink ring-1 ring-inset ring-brand-tint-strong transition-colors hover:bg-brand-tint-strong"
      >
        <QuoteIcon className="h-3.5 w-3.5 text-brand" />
        {citation.document_title}
      </button>
      {open && (
        <span
          role="tooltip"
          className="absolute left-0 top-full z-30 mt-2 block w-72 rounded-card border border-stroke bg-surface p-3.5 text-left shadow-flyout"
        >
          <span className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-brand">
            <QuoteIcon className="h-3 w-3" />
            Foundry IQ citation
          </span>
          <span className="mt-1.5 block text-sm font-semibold text-ink">
            {citation.document_title}
          </span>
          <span className="mt-0.5 block font-mono text-[11px] text-subtle">
            {citation.document_id}
            {citation.page != null ? ` · p.${citation.page}` : ""}
          </span>
          <span className="mt-2.5 block border-l-2 border-brand-tint-strong pl-2.5 text-xs italic leading-relaxed text-ink-secondary">
            “{citation.cited_text}”
          </span>
        </span>
      )}
    </span>
  );
}
