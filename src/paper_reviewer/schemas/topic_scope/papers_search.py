"""Papers search: local ingested Paper hits for a Topic scope."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PaperSearchHit(BaseModel):
    """Bibliographic card for one Paper that matched Papers search."""

    title: str
    url: str
    doi: str
    authors: list[str] = Field(default_factory=list)
    journal: str | None = None
    published_year: int | None = None
    already_referenced: bool
    paper_brief_available: bool


class PapersSearchResult(BaseModel):
    """Hits from Papers search for one Topic scope."""

    hits: list[PaperSearchHit] = Field(default_factory=list)
    truncated: bool = False
