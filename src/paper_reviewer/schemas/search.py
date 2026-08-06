"""Shared search-criteria shapes used by paper-source adapters."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from paper_reviewer.schemas.candidate import PaperCandidate


class SearchStrategy(BaseModel):
    """One named search strategy from generic SearchCriteria."""

    id: str
    label: str
    intent: str | None = None
    concepts: list[str] = Field(default_factory=list)
    synonyms: list[str] = Field(default_factory=list)
    date_from: str | None = None
    date_to: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    retmax: int | None = None


class PubMedStrategyOverride(BaseModel):
    """PubMed-specific override for a strategy id (source_overrides.pubmed)."""

    raw_term: str | None = None
    retmax: int | None = None
    sort: str | None = None


class PubMedSourceOverrides(BaseModel):
    """Opaque PubMed payload under SearchCriteria.source_overrides.pubmed."""

    strategies: dict[str, PubMedStrategyOverride] = Field(default_factory=dict)


class SearchCriteria(BaseModel):
    """Source-agnostic input for related-paper search."""

    strategies: list[SearchStrategy]
    source_overrides: dict[str, Any] = Field(default_factory=dict)


class SourceRunStatus(str, Enum):
    """Per-source outcome for related-paper search."""

    ok = "ok"
    error = "error"
    empty = "empty"


class SourceRun(BaseModel):
    """Status and metadata for one registered paper source run."""

    source_id: str
    status: SourceRunStatus
    hit_count: int = 0
    strategy_ids: list[str] = Field(default_factory=list)
    error: str | None = None


class RelatedPaperSearchResult(BaseModel):
    """Global candidates plus per-source run metadata."""

    candidates: list[PaperCandidate] = Field(default_factory=list)
    source_runs: list[SourceRun] = Field(default_factory=list)
    notes: str | None = None
