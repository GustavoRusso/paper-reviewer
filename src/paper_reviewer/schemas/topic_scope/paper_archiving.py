"""Paper archiving: durable Paper read model and step result types."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Paper(BaseModel):
    """Durable bibliographic record after create-or-reuse."""

    id: int
    created_at: datetime
    doi: str
    source_id: str
    source_uid: str
    title: str
    authors: list[str] = Field(default_factory=list)
    journal: str | None = None
    published_year: int | None = None
    url: str


class ArchiveSkipReason(str, Enum):
    """Policy skip reasons for paper archiving."""

    missing_doi = "missing_doi"
    invalid_required_field = "invalid_required_field"
    doi_conflict = "doi_conflict"


class ArchiveSkip(BaseModel):
    """Expected policy skip for one candidate identity."""

    reason: ArchiveSkipReason
    source_id: str | None = None
    source_uid: str | None = None
    doi: str | None = None


class ArchiveError(BaseModel):
    """Unexpected failure for one candidate after savepoint rollback."""

    reason: str
    source_id: str | None = None
    source_uid: str | None = None
    doi: str | None = None


class PaperArchivingResult(BaseModel):
    """Create-or-reuse outcome for one archive_papers call."""

    papers: list[Paper] = Field(default_factory=list)
    skipped: list[ArchiveSkip] = Field(default_factory=list)
    errors: list[ArchiveError] = Field(default_factory=list)
    created_paper_ids: list[int] = Field(default_factory=list)


class PaperIngestEnqueueResult(BaseModel):
    """Selection outcome after enqueue_regenerate_papers."""

    submitted_paper_ids: list[int] = Field(default_factory=list)
    skipped_already_existed: list[int] = Field(default_factory=list)
