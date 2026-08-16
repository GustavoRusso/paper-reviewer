"""Generate paper brief: enqueue and create-brief result contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field

from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    PaperAspectStatus,
)


class PaperBriefContent(BaseModel):
    """Structured, topic-agnostic LLM brief. Field ids match paper_brief_template.md."""

    summary: str
    objective: str
    study_type: str | None = None
    timeline_geography: str | None = None
    population_sample: str | None = None
    key_methods: str | None = None
    key_findings: list[str]
    discussion: str | None = None
    limitations: str | None = None
    recommendations: str | None = None


class CreatePaperBriefResult(BaseModel):
    """Result of creating or skipping a paper brief for one Paper."""

    paper_id: int
    status: PaperAspectStatus
    error_message: str | None = None


class GeneratePaperBriefsEnqueueResult(BaseModel):
    """Selection outcome after enqueue_generate_paper_briefs."""

    submitted_paper_ids: list[int] = Field(default_factory=list)
    skipped_already_terminal: list[int] = Field(default_factory=list)
