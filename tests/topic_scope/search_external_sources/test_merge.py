"""Merge / dedupe PaperCandidate lists for search external sources."""

from __future__ import annotations

from datetime import date

from paper_reviewer.schemas.topic_scope.search_external_sources import (
    PaperCandidate,
)
from paper_reviewer.topic_scope.search_external_sources.merge import (
    merge_candidates,
)


def _candidate(**overrides: object) -> PaperCandidate:
    base: dict[str, object] = {
        "source_id": "pubmed",
        "source_uid": "1001",
        "doi": "10.1000/EXAMPLE.1001",
        "title": "Example title",
        "authors": ["Author A"],
        "journal": "Nature",
        "published_year": 2022,
        "url": "https://pubmed.ncbi.nlm.nih.gov/1001/",
        "snippet": None,
        "facet_id": "core-concepts",
        "raw_payload_ref": None,
    }
    base.update(overrides)
    return PaperCandidate.model_validate(base)


def test_empty_input_yields_empty_list() -> None:
    assert merge_candidates([]) == []


def test_merge_sorts_newest_year_then_date_with_nulls_last() -> None:
    older = _candidate(
        source_uid="1",
        doi="10.1000/A",
        title="Older",
        published_year=2020,
        pub_date=date(2020, 6, 1),
        url="https://pubmed.ncbi.nlm.nih.gov/1/",
    )
    newer = _candidate(
        source_uid="2",
        doi="10.1000/B",
        title="Newer",
        published_year=2024,
        pub_date=date(2024, 3, 15),
        url="https://pubmed.ncbi.nlm.nih.gov/2/",
    )
    same_year_no_date = _candidate(
        source_uid="3",
        doi="10.1000/C",
        title="Same year, no date",
        published_year=2024,
        pub_date=None,
        url="https://pubmed.ncbi.nlm.nih.gov/3/",
    )
    no_year = _candidate(
        source_uid="4",
        doi="10.1000/D",
        title="No year",
        published_year=None,
        pub_date=None,
        url="https://pubmed.ncbi.nlm.nih.gov/4/",
    )

    merged = merge_candidates([older, no_year, same_year_no_date, newer])

    assert [c.source_uid for c in merged] == ["2", "3", "1", "4"]


def test_dedupe_by_uppercase_doi_keeps_first_then_sorts() -> None:
    first = _candidate(
        source_uid="36328499",
        doi="10.1038/s41586-022-05543-x",
        title="First hit",
        facet_id="core-concepts",
        published_year=2022,
        url="https://pubmed.ncbi.nlm.nih.gov/36328499/",
    )
    duplicate = _candidate(
        source_id="europepmc",
        source_uid="PMC9876543",
        doi="10.1038/S41586-022-05543-X",
        title="Same paper, other source",
        facet_id="broad",
        published_year=2022,
        url="https://europepmc.org/article/PMC/9876543",
    )
    other = _candidate(
        source_uid="11850928",
        doi="10.1126/science.example",
        title="Different DOI",
        published_year=2020,
        url="https://pubmed.ncbi.nlm.nih.gov/11850928/",
    )

    merged = merge_candidates([first, duplicate, other])

    assert [c.source_uid for c in merged] == ["36328499", "11850928"]
    assert [c.title for c in merged] == ["First hit", "Different DOI"]


def test_missing_doi_hits_are_dropped() -> None:
    keep = _candidate(
        source_uid="36328499",
        doi="10.1038/s41586-022-05543-x",
        title="Has DOI",
        url="https://pubmed.ncbi.nlm.nih.gov/36328499/",
    )
    drop_none = _candidate(
        source_uid="11850928",
        doi=None,
        title="No DOI",
        url="https://pubmed.ncbi.nlm.nih.gov/11850928/",
    )
    drop_blank = _candidate(
        source_uid="2",
        doi="   ",
        title="Blank DOI",
        url="https://pubmed.ncbi.nlm.nih.gov/2/",
    )

    merged = merge_candidates([drop_none, keep, drop_blank])
    assert len(merged) == 1
    assert merged[0].source_uid == "36328499"
    assert merged[0].title == "Has DOI"


def test_doi_identity_preferred_over_source_uid() -> None:
    """Two rows with the same DOI merge even when source handles differ."""
    pubmed = _candidate(
        source_id="pubmed",
        source_uid="36328499",
        doi="10.1038/s41586-022-05543-x",
        title="PubMed copy",
        url="https://pubmed.ncbi.nlm.nih.gov/36328499/",
    )
    other = _candidate(
        source_id="europepmc",
        source_uid="PMC9876543",
        doi="10.1038/s41586-022-05543-x",
        title="EuropePMC copy",
        url="https://europepmc.org/article/PMC/9876543",
    )

    merged = merge_candidates([pubmed, other])
    assert len(merged) == 1
    assert merged[0].source_uid == "36328499"
    assert merged[0].title == "PubMed copy"


def test_all_missing_doi_yields_empty_list() -> None:
    a = _candidate(source_uid="1", doi=None, title="A", url="https://pubmed.ncbi.nlm.nih.gov/1/")
    b = _candidate(source_uid="2", doi=None, title="B", url="https://pubmed.ncbi.nlm.nih.gov/2/")

    assert merge_candidates([a, b]) == []


def test_kept_candidates_have_non_null_uppercase_doi() -> None:
    mixed = _candidate(
        source_uid="36328499",
        doi="  10.1038/s41586-022-05543-x  ",
        title="Mixed case",
        published_year=2024,
        url="https://pubmed.ncbi.nlm.nih.gov/36328499/",
    )
    already_upper = _candidate(
        source_uid="11850928",
        doi="10.1126/SCIENCE.EXAMPLE",
        title="Already upper",
        published_year=2022,
        url="https://pubmed.ncbi.nlm.nih.gov/11850928/",
    )

    merged = merge_candidates([mixed, already_upper])

    assert len(merged) == 2
    for candidate in merged:
        assert candidate.doi is not None
        assert candidate.doi == candidate.doi.strip().upper()
        assert candidate.doi == candidate.doi.strip()
    assert merged[0].doi == "10.1038/S41586-022-05543-X"
    assert merged[1].doi == "10.1126/SCIENCE.EXAMPLE"
