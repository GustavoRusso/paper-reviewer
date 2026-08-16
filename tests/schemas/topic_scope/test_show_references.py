"""Show references list contracts."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from paper_reviewer.schemas.topic_brief_generation.show_references import (
    ReferencedPaper,
    ShowReferencesResult,
)


def _sample_paper(**overrides: object) -> ReferencedPaper:
    data: dict[str, object] = {
        "title": "Example title",
        "url": "https://pubmed.ncbi.nlm.nih.gov/12345/",
        "doi": "10.1000/EXAMPLE",
        "authors": ["Ada Lovelace"],
        "journal": "Nature",
        "published_year": 2024,
        "referenced_at": datetime(2026, 8, 16, tzinfo=UTC),
        "paper_brief_available": False,
    }
    data.update(overrides)
    return ReferencedPaper.model_validate(data)


def test_referenced_paper_construction() -> None:
    paper = _sample_paper()

    assert paper.title == "Example title"
    assert paper.url == "https://pubmed.ncbi.nlm.nih.gov/12345/"
    assert paper.doi == "10.1000/EXAMPLE"
    assert paper.authors == ["Ada Lovelace"]
    assert paper.journal == "Nature"
    assert paper.published_year == 2024
    assert paper.referenced_at == datetime(2026, 8, 16, tzinfo=UTC)
    assert paper.paper_brief_available is False


def test_referenced_paper_paper_brief_available() -> None:
    paper = _sample_paper(paper_brief_available=True)

    assert paper.paper_brief_available is True


def test_referenced_paper_allows_empty_authors_and_optional_fields() -> None:
    paper = _sample_paper(authors=[], journal=None, published_year=None)

    assert paper.authors == []
    assert paper.journal is None
    assert paper.published_year is None


def test_referenced_paper_requires_title_url_doi_referenced_at_and_brief_flag() -> None:
    with pytest.raises(ValidationError):
        ReferencedPaper.model_validate(
            {
                "title": "Example title",
                "url": "https://example.com/1",
                "doi": "10.1000/EXAMPLE",
                "authors": [],
            }
        )

    with pytest.raises(ValidationError):
        ReferencedPaper.model_validate(
            {
                "title": "Example title",
                "url": "https://example.com/1",
                "doi": "10.1000/EXAMPLE",
                "authors": [],
                "referenced_at": datetime(2026, 8, 16, tzinfo=UTC),
            }
        )


def test_show_references_result_defaults_to_empty_list() -> None:
    result = ShowReferencesResult()

    assert result.papers == []


def test_show_references_result_holds_papers() -> None:
    paper = _sample_paper()
    result = ShowReferencesResult(papers=[paper])

    assert result.papers == [paper]
