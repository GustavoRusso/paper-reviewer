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
    """Result of the default-skip fulfill orchestrator for one Paper."""

    paper_id: int
    source_record: InformSourceRecordResult
    full_text: InformFullTextResult


class FulfillPapersMetadataEnqueueResult(BaseModel):
    """Selection outcome after enqueue_fulfill_papers_metadata."""

    submitted_paper_ids: list[int] = Field(default_factory=list)
    skipped_already_terminal: list[int] = Field(default_factory=list)


class IngestPaperResult(BaseModel):
    """Result of the ingest_paper orchestrator for one Paper.

    ``brief`` is a ``CreatePaperBriefResult`` or ``None``. ``evaluation`` is an
    ``EvaluatePaperBriefResult`` or ``None``. Nested types live in generate
    paper brief and paper brief evaluation schemas; these fields stay untyped
    here so the schema modules do not import each other.
    """

    paper_id: int
    source_record: InformSourceRecordResult
    full_text: InformFullTextResult
    brief: object | None = None
    evaluation: object | None = None
