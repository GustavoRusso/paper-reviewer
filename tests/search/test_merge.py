"""Merge / dedupe PaperCandidate lists for related-paper search."""

from __future__ import annotations

from paper_reviewer.schemas.candidate import PaperCandidate
from paper_reviewer.search.merge import merge_candidates


def _candidate(**overrides: object) -> PaperCandidate:
    base: dict[str, object] = {
        "source_id": "pubmed",
        "source_uid": "1001",
        "doi": None,
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


def test_unique_candidates_preserved_in_order() -> None:
    a = _candidate(source_uid="1", title="First", url="https://pubmed.ncbi.nlm.nih.gov/1/")
    b = _candidate(source_uid="2", title="Second", url="https://pubmed.ncbi.nlm.nih.gov/2/")

    assert merge_candidates([a, b]) == [a, b]


def test_dedupe_by_case_normalized_doi_keeps_first() -> None:
    first = _candidate(
        source_uid="36328499",
        doi="10.1038/s41586-022-05543-x",
        title="First hit",
        facet_id="core-concepts",
        url="https://pubmed.ncbi.nlm.nih.gov/36328499/",
    )
    duplicate = _candidate(
        source_id="europepmc",
        source_uid="PMC9876543",
        doi="10.1038/S41586-022-05543-X",
        title="Same paper, other source",
        facet_id="broad",
        url="https://europepmc.org/article/PMC/9876543",
    )
    other = _candidate(
        source_uid="11850928",
        doi="10.1126/science.example",
        title="Different DOI",
        url="https://pubmed.ncbi.nlm.nih.gov/11850928/",
    )

    merged = merge_candidates([first, duplicate, other])

    assert merged == [first, other]


def test_dedupe_by_source_id_and_uid_when_doi_missing() -> None:
    first = _candidate(
        source_uid="11850928",
        doi=None,
        title="First without DOI",
        facet_id="core-concepts",
        url="https://pubmed.ncbi.nlm.nih.gov/11850928/",
    )
    duplicate = _candidate(
        source_uid="11850928",
        doi=None,
        title="Same pubmed uid, later strategy",
        facet_id="broad",
        url="https://pubmed.ncbi.nlm.nih.gov/11850928/",
    )
    other_source_same_uid = _candidate(
        source_id="europepmc",
        source_uid="11850928",
        doi=None,
        title="Same uid, different source",
        url="https://europepmc.org/article/MED/11850928",
    )

    merged = merge_candidates([first, duplicate, other_source_same_uid])

    assert merged == [first, other_source_same_uid]


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

    assert merge_candidates([pubmed, other]) == [pubmed]


def test_missing_doi_does_not_collapse_unrelated_rows() -> None:
    a = _candidate(source_uid="1", doi=None, title="A", url="https://pubmed.ncbi.nlm.nih.gov/1/")
    b = _candidate(source_uid="2", doi=None, title="B", url="https://pubmed.ncbi.nlm.nih.gov/2/")

    assert merge_candidates([a, b]) == [a, b]
