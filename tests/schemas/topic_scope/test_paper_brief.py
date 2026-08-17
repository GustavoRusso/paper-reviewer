"""Paper brief read contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    PaperBriefContent,
)
from paper_reviewer.schemas.topic_scope.paper_brief import (
    PaperBriefRead,
    PaperBriefReadStatus,
)


def _sample_content() -> PaperBriefContent:
    return PaperBriefContent(
        summary="Why it matters.",
        objective="Close a knowledge gap.",
        key_findings=["Finding one"],
    )


def test_paper_brief_read_status_members() -> None:
    assert list(PaperBriefReadStatus) == [
        PaperBriefReadStatus.ready,
        PaperBriefReadStatus.paper_missing,
        PaperBriefReadStatus.brief_unavailable,
        PaperBriefReadStatus.invalid_content,
    ]


def test_paper_brief_read_ready() -> None:
    content = _sample_content()
    result = PaperBriefRead(
        status=PaperBriefReadStatus.ready,
        doi="10.1000/EXAMPLE",
        title="Example title",
        url="https://example.com/1",
        authors=["Ada Lovelace"],
        journal="Nature",
        published_year=2024,
        content=content,
    )

    assert result.status is PaperBriefReadStatus.ready
    assert result.doi == "10.1000/EXAMPLE"
    assert result.title == "Example title"
    assert result.url == "https://example.com/1"
    assert result.authors == ["Ada Lovelace"]
    assert result.journal == "Nature"
    assert result.published_year == 2024
    assert result.content == content
    assert "id" not in PaperBriefRead.model_fields
    assert "paper_id" not in PaperBriefRead.model_fields


def test_paper_brief_read_paper_missing_has_no_bibliographic_fields() -> None:
    result = PaperBriefRead(
        status=PaperBriefReadStatus.paper_missing,
        doi="10.1000/MISSING",
    )

    assert result.title is None
    assert result.url is None
    assert result.authors == []
    assert result.journal is None
    assert result.published_year is None
    assert result.content is None


def test_paper_brief_read_requires_status_and_doi() -> None:
    with pytest.raises(ValidationError):
        PaperBriefRead.model_validate({"doi": "10.1000/EXAMPLE"})
