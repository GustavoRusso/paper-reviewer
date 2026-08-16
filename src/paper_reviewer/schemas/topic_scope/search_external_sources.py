"""Search external sources criteria, candidates, and run metadata."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from paper_reviewer.schemas.topic_brief_generation.topic_analysis import (
    TopicAnalysisResult,
)


class PaperCandidate(BaseModel):
    """Normalized hit from an external source for Search external sources.

    Source maps may omit ``doi``. After Search external sources merge, every
    candidate has a non-blank uppercase ``doi``.
    """

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


class PubMedFacetOverride(BaseModel):
    """PubMed-specific override for a facet id (source_overrides.pubmed)."""

    raw_term: str | None = None
    retmax: int | None = None
    sort: str | None = None


class PubMedSourceOverrides(BaseModel):
    """Opaque PubMed payload under SearchCriteria.source_overrides.pubmed."""

    facets: dict[str, PubMedFacetOverride] = Field(default_factory=dict)


class SearchCriteria(BaseModel):
    """Source-agnostic input for Search external sources."""

    topic_analysis: TopicAnalysisResult
    source_overrides: dict[str, Any] = Field(default_factory=dict)


class SourceRunStatus(str, Enum):
    """Per-source outcome for Search external sources."""

    ok = "ok"
    error = "error"
    empty = "empty"


class SourceRun(BaseModel):
    """Status and metadata for one registered external source run."""

    source_id: str
    status: SourceRunStatus
    hit_count: int = 0
    facet_ids: list[str] = Field(default_factory=list)
    error: str | None = None


class SearchExternalSourcesResult(BaseModel):
    """Global candidates plus per-source run metadata."""

    candidates: list[PaperCandidate] = Field(default_factory=list)
    source_runs: list[SourceRun] = Field(default_factory=list)
    notes: str | None = None
