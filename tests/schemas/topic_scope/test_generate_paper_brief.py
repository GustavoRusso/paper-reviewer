"""Generate paper brief: Pydantic content and result contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    CreatePaperBriefResult,
    GeneratePaperBriefsEnqueueResult,
    PaperBriefContent,
)
from paper_reviewer.topic_scope.generate_paper_brief.llm import (
    template_field_ids,
)


def test_paper_brief_content_requires_summary_objective_and_findings() -> None:
    content = PaperBriefContent(
        summary="Why it matters.",
        objective="Close a knowledge gap.",
        key_findings=["Finding one"],
    )

    assert content.summary == "Why it matters."
    assert content.objective == "Close a knowledge gap."
    assert content.key_findings == ["Finding one"]
    assert content.study_type is None
    assert content.limitations is None


def test_paper_brief_content_rejects_missing_required() -> None:
    with pytest.raises(ValidationError):
        PaperBriefContent.model_validate({"summary": "Only summary."})


def test_paper_brief_content_has_no_relevance_to_topic() -> None:
    assert "relevance_to_topic" not in PaperBriefContent.model_fields


def test_paper_brief_content_fields_match_template_front_matter() -> None:
    assert list(PaperBriefContent.model_fields) == template_field_ids()


def test_create_paper_brief_result() -> None:
    result = CreatePaperBriefResult(
        paper_id=10,
        status=PaperAspectStatus.succeeded,
    )

    assert result.paper_id == 10
    assert result.status is PaperAspectStatus.succeeded
    assert result.error_message is None


def test_enqueue_result_lists() -> None:
    result = GeneratePaperBriefsEnqueueResult(
        submitted_paper_ids=[10],
        skipped_already_terminal=[11, 12],
    )

    assert result.submitted_paper_ids == [10]
    assert result.skipped_already_terminal == [11, 12]
