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


class InformSourceRecordResult(BaseModel):
    """Result of informing the source-record aspect for one Paper."""

    paper_id: int
    status: PaperAspectStatus
    error_message: str | None = None


class InformFullTextResult(BaseModel):
    """Result of informing the full-text aspect for one Paper."""

    paper_id: int
    status: PaperAspectStatus
    error_message: str | None = None


class FulfillPaperMetadataResult(BaseModel):
    """Result of the page-6 orchestrator for one Paper."""

    paper_id: int
    source_record: InformSourceRecordResult
    full_text: InformFullTextResult


class FulfillPapersMetadataEnqueueResult(BaseModel):
    """Selection outcome after enqueue_fulfill_papers_metadata."""

    submitted_paper_ids: list[int] = Field(default_factory=list)
    skipped_already_terminal: list[int] = Field(default_factory=list)


class RegeneratePaperResult(BaseModel):
    """Result of the force regenerate orchestrator for one Paper.

    ``brief`` is a ``CreatePaperBriefResult`` or ``None``. The nested type lives
    in generate_paper_brief schemas; this field stays untyped here so the two
    schema modules do not import each other.
    """

    paper_id: int
    source_record: InformSourceRecordResult
    full_text: InformFullTextResult
    brief: object | None = None
