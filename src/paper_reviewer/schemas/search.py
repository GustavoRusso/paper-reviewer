"""Shared search-criteria shapes used by paper-source adapters."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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
