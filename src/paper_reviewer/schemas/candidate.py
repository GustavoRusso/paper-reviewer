"""Shared paper-candidate shapes used across paper sources."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PaperCandidate(BaseModel):
    """Normalized hit from a paper source for related-paper search triage."""

    source_id: str
    source_uid: str
    doi: str | None = None
    title: str
    authors: list[str] = Field(default_factory=list)
    journal: str | None = None
    published_year: int | None = None
    url: str
    snippet: str | None = None
    facet_id: str
    raw_payload_ref: str | None = None
