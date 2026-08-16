"""Topic brief generation: Pydantic content and result contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.topic_brief_generation import (
    CreateTopicBriefEnqueueResult,
    CreateTopicBriefResult,
    TopicBriefContent,
)
from paper_reviewer.topic_scope.topic_brief_generation.template import (
    template_field_ids,
)


def test_topic_brief_content_requires_core_fields() -> None:
    content = TopicBriefContent(
        title="Example topic brief title for indexing",
        abstract="A short abstract.",
        introduction="Background.[1]",
        sections=[{"heading": "Theme", "body": "Body.[1]"}],
        concluding_section="Closing.",
        key_points=["Point one"],
        citations=[{"n": 1, "doi": "10.1000/A", "text": "10.1000/A — Title"}],
    )

    assert content.title.startswith("Example")
    assert content.sections[0].heading == "Theme"
    assert content.citations[0].n == 1


def test_topic_brief_content_rejects_missing_required() -> None:
    with pytest.raises(ValidationError):
        TopicBriefContent.model_validate({"title": "Only title."})


def test_topic_brief_content_fields_match_template_front_matter() -> None:
    assert list(TopicBriefContent.model_fields) == template_field_ids()


def test_create_topic_brief_result() -> None:
    result = CreateTopicBriefResult(
        topic_scope_id=10,
        status=PaperAspectStatus.succeeded,
    )

    assert result.topic_scope_id == 10
    assert result.status is PaperAspectStatus.succeeded
    assert result.error_message is None


def test_enqueue_result_flags() -> None:
    submitted = CreateTopicBriefEnqueueResult(submitted=True)
    in_flight = CreateTopicBriefEnqueueResult(skipped_in_flight=True)
    no_briefed = CreateTopicBriefEnqueueResult(skipped_no_briefed=True)

    assert submitted.submitted is True
    assert in_flight.skipped_in_flight is True
    assert no_briefed.skipped_no_briefed is True
