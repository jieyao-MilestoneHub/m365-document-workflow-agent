"use client";

import { useState } from "react";

import type { Citation } from "@/lib/types";

/**
 * Foundry IQ citation popover. Shows the source document title and the exact cited snippet
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
        className="inline-flex items-center gap-1 rounded bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700 ring-1 ring-inset ring-indigo-200 hover:bg-indigo-100"
      >
        <span aria-hidden>¶</span>
        {citation.document_title}
      </button>
      {open && (
        <span
          role="tooltip"
          className="absolute left-0 top-full z-10 mt-1 block w-72 rounded-md border border-slate-200 bg-white p-3 text-left shadow-lg"
        >
          <span className="block text-xs font-semibold text-slate-800">
            {citation.document_title}
          </span>
          <span className="mt-1 block font-mono text-xs text-slate-500">
            {citation.document_id}
            {citation.page != null ? ` · p.${citation.page}` : ""}
          </span>
          <span className="mt-2 block border-l-2 border-indigo-200 pl-2 text-xs italic text-slate-700">
            “{citation.cited_text}”
          </span>
        </span>
      )}
    </span>
  );
}
