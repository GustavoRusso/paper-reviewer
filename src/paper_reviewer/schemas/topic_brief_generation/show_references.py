"""Show references: list of Papers already linked to a Topic scope."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReferencedPaper(BaseModel):
    """Bibliographic card for one Paper that is a Reference for a Topic scope."""

    title: str
    url: str
    doi: str
    authors: list[str] = Field(default_factory=list)
    journal: str | None = None
    published_year: int | None = None
    referenced_at: datetime


class ShowReferencesResult(BaseModel):
    """Papers already selected as References for one Topic scope."""

    papers: list[ReferencedPaper] = Field(default_factory=list)
