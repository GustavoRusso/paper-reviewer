"""Fulfill papers metadata: enqueue and inform result contracts."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class PaperAspectStatus(str, Enum):
    """Stored status of one paper aspect (source record, full text, later brief)."""

    not_started = "not_started"
    succeeded = "succeeded"
    failed = "failed"
    unavailable = "unavailable"


class InformOutcome(str, Enum):
    """Outcome of one inform_paper_from_source run."""

    skipped_already_informed = "skipped_already_informed"
    fulfilled = "fulfilled"
    failed = "failed"
    unavailable = "unavailable"


class InformPaperFromSourceResult(BaseModel):
    """Result of informing one Paper from its source."""

    paper_id: int
    outcome: InformOutcome
    error_message: str | None = None
    source_record_status: PaperAspectStatus = PaperAspectStatus.not_started
    full_text_status: PaperAspectStatus = PaperAspectStatus.not_started
    source_record_error_message: str | None = None
    full_text_error_message: str | None = None


class FulfillPapersMetadataEnqueueResult(BaseModel):
    """Selection outcome after enqueue_fulfill_papers_metadata."""

    submitted_paper_ids: list[int] = Field(default_factory=list)
    skipped_already_informed: list[int] = Field(default_factory=list)
    skipped_already_failed: list[int] = Field(default_factory=list)
