"""PaperCandidate parsing and DocSum → candidate mapping."""

from __future__ import annotations

from paper_reviewer.ingest.pubmed.mapping import docsum_to_candidate
from paper_reviewer.schemas.topic_brief_generation.search_external_sources import (
    PaperCandidate,
)

# Real-shaped ESummary JSON DocSum (retmode=json), trimmed to fields we map.
DOCSUM_WITH_DOI = {
    "uid": "36328499",
    "pubdate": "2022 Dec 15",
    "epubdate": "2022 Nov 2",
    "source": "Nature",
    "authors": [
        {"name": "Smith J", "authtype": "Author", "clusterid": ""},
        {"name": "Jones M", "authtype": "Author", "clusterid": ""},
    ],
    "lastauthor": "Jones M",
    "title": "Example article title about CRISPR gene editing.",
    "sorttitle": "example article title about crispr gene editing",
    "fulljournalname": "Nature",
    "articleids": [
        {"idtype": "pubmed", "idtypen": 1, "value": "36328499"},
        {"idtype": "doi", "idtypen": 3, "value": "10.1038/s41586-022-05543-x"},
        {"idtype": "pmc", "idtypen": 8, "value": "PMC9876543"},
    ],
    "attributes": ["Has Abstract"],
}

DOCSUM_WITHOUT_DOI = {
    "uid": "11850928",
    "pubdate": "2002 Apr",
    "epubdate": "",
    "source": "Science",
    "authors": [
        {"name": "Doe A", "authtype": "Author", "clusterid": ""},
    ],
    "title": "A paper without a DOI in articleids.",
    "fulljournalname": "Science (New York, N.Y.)",
    "articleids": [
        {"idtype": "pubmed", "idtypen": 1, "value": "11850928"},
    ],
    "attributes": [],
}


def test_paper_candidate_parses_required_and_optional_fields() -> None:
    candidate = PaperCandidate.model_validate(
        {
            "source_id": "pubmed",
            "source_uid": "36328499",
            "doi": "10.1038/s41586-022-05543-x",
            "title": "Example article title about CRISPR gene editing.",
            "authors": ["Smith J", "Jones M"],
            "journal": "Nature",
            "published_year": 2022,
            "url": "https://pubmed.ncbi.nlm.nih.gov/36328499/",
            "snippet": None,
            "facet_id": "core-concepts",
            "raw_payload_ref": None,
        }
    )
    assert candidate.source_id == "pubmed"
    assert candidate.source_uid == "36328499"
    assert candidate.doi == "10.1038/s41586-022-05543-x"
    assert candidate.authors == ["Smith J", "Jones M"]
    assert candidate.published_year == 2022
    assert candidate.snippet is None
    assert candidate.facet_id == "core-concepts"


def test_docsum_with_doi_maps_to_candidate() -> None:
    candidate = docsum_to_candidate(DOCSUM_WITH_DOI, facet_id="fixture-pubmed")

    assert candidate.source_id == "pubmed"
    assert candidate.source_uid == "36328499"
    assert candidate.doi == "10.1038/s41586-022-05543-x"
    assert candidate.title == "Example article title about CRISPR gene editing."
    assert candidate.authors == ["Smith J", "Jones M"]
    assert candidate.journal == "Nature"
    assert candidate.published_year == 2022
    assert candidate.url == "https://pubmed.ncbi.nlm.nih.gov/36328499/"
    assert candidate.snippet is None
    assert candidate.facet_id == "fixture-pubmed"


def test_docsum_missing_doi_yields_null_doi() -> None:
    candidate = docsum_to_candidate(DOCSUM_WITHOUT_DOI, facet_id="core-concepts")

    assert candidate.doi is None
    assert candidate.source_uid == "11850928"
    assert candidate.url == "https://pubmed.ncbi.nlm.nih.gov/11850928/"
    assert candidate.facet_id == "core-concepts"


def test_docsum_missing_snippet_omits_snippet() -> None:
    """Standard DocSums have no short text field — snippet stays unset."""
    candidate = docsum_to_candidate(DOCSUM_WITH_DOI, facet_id="core-concepts")

    assert candidate.snippet is None


def test_docsum_with_usable_snippet_maps_snippet() -> None:
    docsum = {
        **DOCSUM_WITH_DOI,
        "snippet": "Short search-hit text already returned by the API.",
    }

    candidate = docsum_to_candidate(docsum, facet_id="core-concepts")

    assert candidate.snippet == "Short search-hit text already returned by the API."


def test_journal_falls_back_to_source_when_fulljournalname_absent() -> None:
    docsum = {
        "uid": "1",
        "pubdate": "2020 Jan 1",
        "source": "Lancet",
        "authors": [],
        "title": "Fallback journal name",
        "articleids": [{"idtype": "pubmed", "idtypen": 1, "value": "1"}],
    }

    candidate = docsum_to_candidate(docsum, facet_id="s")

    assert candidate.journal == "Lancet"
    assert candidate.published_year == 2020
