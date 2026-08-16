"""Topic brief generation: Pydantic content and result contracts."""

from __future__ import annotations

from pydantic import BaseModel

from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)


class TopicBriefSection(BaseModel):
    """One first-level section in a topic brief."""

    heading: str
    body: str


class TopicBriefCitation(BaseModel):
    """One bibliography entry echoed from an app citation_description."""

    n: int
    doi: str
    text: str


class TopicBriefContent(BaseModel):
    """Structured topic-conditioned brief. Field ids match topic_brief_template.md."""

    title: str
    abstract: str
    introduction: str
    sections: list[TopicBriefSection]
    concluding_section: str
    key_points: list[str]
    citations: list[TopicBriefCitation]


class CreateTopicBriefResult(BaseModel):
    """Result of creating or failing a topic brief for one Topic scope."""

    topic_scope_id: int
    status: PaperAspectStatus
    error_message: str | None = None


class CreateTopicBriefEnqueueResult(BaseModel):
    """Selection outcome after enqueue_create_topic_brief."""

    submitted: bool = False
    skipped_in_flight: bool = False
    skipped_no_briefed: bool = False
