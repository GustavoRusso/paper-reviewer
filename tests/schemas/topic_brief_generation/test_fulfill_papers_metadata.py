"""Fulfill papers metadata: Pydantic result contracts."""

from __future__ import annotations

from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    InformFullTextResult,
    InformSourceRecordResult,
    PaperAspectStatus,
    RegeneratePaperResult,
)
from paper_reviewer.schemas.topic_brief_generation.generate_paper_brief import (
    CreatePaperBriefResult,
)


def test_regenerate_paper_result_brief_none_when_full_text_not_succeeded() -> None:
    result = RegeneratePaperResult(
        paper_id=10,
        source_record=InformSourceRecordResult(
            paper_id=10,
            status=PaperAspectStatus.succeeded,
        ),
        full_text=InformFullTextResult(
            paper_id=10,
            status=PaperAspectStatus.unavailable,
        ),
        brief=None,
    )

    assert result.paper_id == 10
    assert result.source_record.status is PaperAspectStatus.succeeded
    assert result.full_text.status is PaperAspectStatus.unavailable
    assert result.brief is None


def test_regenerate_paper_result_includes_brief_when_present() -> None:
    result = RegeneratePaperResult(
        paper_id=10,
        source_record=InformSourceRecordResult(
            paper_id=10,
            status=PaperAspectStatus.succeeded,
        ),
        full_text=InformFullTextResult(
            paper_id=10,
            status=PaperAspectStatus.succeeded,
        ),
        brief=CreatePaperBriefResult(
            paper_id=10,
            status=PaperAspectStatus.succeeded,
        ),
    )

    assert result.brief is not None
    assert result.brief.status is PaperAspectStatus.succeeded
