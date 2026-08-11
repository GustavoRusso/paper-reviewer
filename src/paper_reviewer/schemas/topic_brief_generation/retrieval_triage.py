"""Retrieval triage: retained candidates after human confirm."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from paper_reviewer.schemas.topic_brief_generation.related_paper_search import (
    PaperCandidate,
)


class TriageRejection(BaseModel):
    """Identity and reason for a discarded candidate (future manual discard)."""

    source_id: str
    source_uid: str
    doi: str | None = None
    reason: str


class RetrievalTriageResult(BaseModel):
    """Outcome of retrieval triage for one Topic brief generation."""

    retained: list[PaperCandidate] = Field(default_factory=list)
    rejected: list[TriageRejection] = Field(default_factory=list)
    confirmed_at: datetime | None = None
