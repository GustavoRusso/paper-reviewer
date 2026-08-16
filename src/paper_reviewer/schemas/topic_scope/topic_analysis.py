"""Topic analysis: facet shapes for one TopicScope."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TopicFacet(BaseModel):
    """One named facet distilled from a topic statement."""

    id: str
    label: str
    intent: str | None = None
    concepts: list[str] = Field(default_factory=list)
    synonyms: list[str] = Field(default_factory=list)
    date_from: str | None = None
    date_to: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    retmax: int | None = None


class TopicAnalysisResult(BaseModel):
    """Topic analysis output: facets for one TopicScope."""

    facets: list[TopicFacet]
