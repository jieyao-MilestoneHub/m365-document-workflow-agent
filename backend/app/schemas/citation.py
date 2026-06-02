"""Foundry IQ citation — a traceable pointer to a source document snippet.

Every grounded claim (matched PO line, policy rule applied, promotion agreement) should carry
citations so the UI can show a reviewer exactly what the agent relied on. ``cited_text`` is the
exact snippet.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Citation(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_id: str
    document_title: str
    cited_text: str
    #: optional locators within the source document
    page: int | None = None
    start_char: int | None = None
    end_char: int | None = None
