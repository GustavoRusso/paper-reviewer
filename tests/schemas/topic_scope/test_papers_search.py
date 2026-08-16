"""Papers search schemas: hit and result contracts."""

from __future__ import annotations

from paper_reviewer.schemas.topic_brief_generation.papers_search import (
    PaperSearchHit,
    PapersSearchResult,
)


def test_paper_search_hit_fields() -> None:
    hit = PaperSearchHit(
        title="Example",
        url="https://example.com/1",
        doi="10.1000/A",
        authors=["Ada"],
        journal="Nature",
        published_year=2024,
        already_referenced=True,
        paper_brief_available=False,
    )

    assert hit.title == "Example"
    assert hit.doi == "10.1000/A"
    assert hit.already_referenced is True
    assert hit.paper_brief_available is False
    assert not hasattr(hit, "id") or "id" not in hit.model_fields


def test_paper_search_hit_paper_brief_available() -> None:
    hit = PaperSearchHit(
        title="Example",
        url="https://example.com/1",
        doi="10.1000/A",
        authors=[],
        journal=None,
        published_year=None,
        already_referenced=False,
        paper_brief_available=True,
    )

    assert hit.paper_brief_available is True


def test_papers_search_result_defaults() -> None:
    result = PapersSearchResult()

    assert result.hits == []
    assert result.truncated is False
