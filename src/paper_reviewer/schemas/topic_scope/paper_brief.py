"""Paper brief read: succeeded global PaperBrief by DOI."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field

from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    PaperBriefContent,
)


class PaperBriefReadStatus(str, Enum):
    """Outcome of loading a paper brief for the reader page."""

    ready = "ready"
    paper_missing = "paper_missing"
    brief_unavailable = "brief_unavailable"
    invalid_content = "invalid_content"


class PaperBriefRead(BaseModel):
    """Bibliographic header plus optional PaperBriefContent for one DOI."""

    status: PaperBriefReadStatus
    doi: str
    title: str | None = None
    url: str | None = None
    authors: list[str] = Field(default_factory=list)
    journal: str | None = None
    published_year: int | None = None
    content: PaperBriefContent | None = None
    evaluation_score: Decimal | None = None
