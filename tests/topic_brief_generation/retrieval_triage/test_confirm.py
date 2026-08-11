"""Retrieval triage: confirm pass-through to retained candidates."""

from __future__ import annotations

from paper_reviewer.schemas.topic_brief_generation.related_paper_search import (
    PaperCandidate,
    RelatedPaperSearchResult,
    SourceRun,
    SourceRunStatus,
)
from paper_reviewer.topic_brief_generation.retrieval_triage import (
    confirm_retrieval_triage,
)


def _candidate(**overrides: object) -> PaperCandidate:
    data: dict[str, object] = {
        "source_id": "pubmed",
        "source_uid": "100",
        "doi": "10.1000/EXAMPLE",
        "title": "Example title",
        "authors": ["Ada Lovelace"],
        "journal": "Nature",
        "published_year": 2024,
        "url": "https://pubmed.ncbi.nlm.nih.gov/100/",
        "snippet": "snippet text",
        "facet_id": "facet-1",
        "raw_payload_ref": "ref-1",
    }
    data.update(overrides)
    return PaperCandidate.model_validate(data)


def test_confirm_retains_all_candidates_in_order() -> None:
    first = _candidate(source_uid="1", doi="10.1000/A")
    second = _candidate(source_uid="2", doi="10.1000/B")
    search_result = RelatedPaperSearchResult(
        candidates=[first, second],
        source_runs=[
            SourceRun(
                source_id="pubmed",
                status=SourceRunStatus.ok,
                hit_count=2,
                facet_ids=["facet-1"],
            )
        ],
    )

    result = confirm_retrieval_triage(search_result)

    assert result.retained == [first, second]
    assert result.rejected == []
    assert result.confirmed_at is None


def test_confirm_empty_candidates_returns_empty_retained() -> None:
    search_result = RelatedPaperSearchResult(candidates=[], source_runs=[])

    result = confirm_retrieval_triage(search_result)

    assert result.retained == []
    assert result.rejected == []
    assert result.confirmed_at is None
