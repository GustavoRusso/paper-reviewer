"""Related-paper search: SearchCriteria, orchestration, fail-soft."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import responses

from paper_reviewer.ingest.pubmed.config import EUTILS_BASE_URL
from paper_reviewer.schemas.topic_brief_generation.related_paper_search import (
    PaperCandidate,
    SearchCriteria,
    SourceRunStatus,
)
from paper_reviewer.topic_brief_generation.related_paper_search.orchestrate import (
    search_related_papers,
)
from tests.ingest.pubmed.test_config import ESEARCH_JSON, ESUMMARY_JSON


CRITERIA_FIXTURE = {
    "topic_analysis": {
        "facets": [
            {
                "id": "core-concepts",
                "label": "Core concepts",
                "intent": "Narrow topical match",
                "concepts": ["glioblastoma", "immunotherapy"],
                "synonyms": ["GBM"],
                "date_from": "2018-01-01",
                "date_to": None,
                "filters": {},
                "retmax": 50,
            }
        ]
    },
    "source_overrides": {
        "pubmed": {
            "facets": {
                "core-concepts": {
                    "raw_term": (
                        "glioblastoma[mesh] AND immunotherapy[Title/Abstract] "
                        "AND 2018:3000[pdat]"
                    )
                }
            }
        }
    },
}


def _stub_pubmed_http(rsps: responses.RequestsMock) -> None:
    rsps.add(
        responses.GET,
        f"{EUTILS_BASE_URL}esearch.fcgi",
        json=ESEARCH_JSON,
    )
    rsps.add(
        responses.GET,
        f"{EUTILS_BASE_URL}esummary.fcgi",
        json=ESUMMARY_JSON,
    )


def test_search_criteria_parses_spec_fixture() -> None:
    criteria = SearchCriteria.model_validate(CRITERIA_FIXTURE)

    assert len(criteria.topic_analysis.facets) == 1
    facet = criteria.topic_analysis.facets[0]
    assert facet.id == "core-concepts"
    assert facet.label == "Core concepts"
    assert facet.intent == "Narrow topical match"
    assert facet.concepts == ["glioblastoma", "immunotherapy"]
    assert facet.synonyms == ["GBM"]
    assert facet.date_from == "2018-01-01"
    assert facet.date_to is None
    assert facet.filters == {}
    assert facet.retmax == 50
    assert "pubmed" in criteria.source_overrides
    pubmed_override = criteria.source_overrides["pubmed"]
    assert pubmed_override["facets"]["core-concepts"]["raw_term"].startswith(
        "glioblastoma[mesh]"
    )


def test_empty_facets_yields_empty_candidates_with_note() -> None:
    criteria = SearchCriteria.model_validate(
        {"topic_analysis": {"facets": []}, "source_overrides": {}}
    )

    result = search_related_papers(criteria)

    assert result.candidates == []
    assert result.source_runs == []
    assert result.notes is not None
    assert "no facets" in result.notes.casefold()


def test_orchestrate_pubmed_with_override_returns_candidates_and_ok_run() -> None:
    criteria = SearchCriteria.model_validate(CRITERIA_FIXTURE)

    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        _stub_pubmed_http(rsps)
        result = search_related_papers(criteria, api_key="TESTKEY")

        esearch_urls = [
            call.request.url
            for call in rsps.calls
            if call.request.url and "esearch.fcgi" in call.request.url
        ]
        assert esearch_urls
        esearch_qs = parse_qs(urlparse(esearch_urls[0]).query)
        assert esearch_qs["term"] == [
            "glioblastoma[mesh] AND immunotherapy[Title/Abstract] AND 2018:3000[pdat]"
        ]
        assert esearch_qs["api_key"] == ["TESTKEY"]

    assert len(result.candidates) == 2
    assert all(isinstance(c, PaperCandidate) for c in result.candidates)
    assert all(c.source_id == "pubmed" for c in result.candidates)
    assert all(c.facet_id == "core-concepts" for c in result.candidates)
    assert result.candidates[0].source_uid == "21256409"

    assert len(result.source_runs) == 1
    run = result.source_runs[0]
    assert run.source_id == "pubmed"
    assert run.status == SourceRunStatus.ok
    assert run.hit_count == 2
    assert run.facet_ids == ["core-concepts"]
    assert run.error is None


def test_source_zero_hits_records_empty_status() -> None:
    criteria = SearchCriteria.model_validate(
        {
            "topic_analysis": {
                "facets": [
                    {
                        "id": "fixture-narrow",
                        "label": "Fixture narrow",
                        "concepts": ["nosuchterm"],
                        "retmax": 20,
                    }
                ]
            },
            "source_overrides": {
                "pubmed": {
                    "facets": {
                        "fixture-narrow": {"raw_term": "nosuchterm[mesh]"}
                    }
                }
            },
        }
    )
    empty_esearch = {
        "header": {"type": "esearch", "version": "0.3"},
        "esearchresult": {
            "count": "0",
            "retmax": "0",
            "retstart": "0",
            "querykey": "1",
            "webenv": "MCID_EMPTY",
            "idlist": [],
            "translationset": [],
            "querytranslation": "nosuchterm[MeSH Terms]",
        },
    }
    empty_esummary = {
        "header": {"type": "esummary", "version": "0.3"},
        "result": {"uids": []},
    }

    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            responses.GET,
            f"{EUTILS_BASE_URL}esearch.fcgi",
            json=empty_esearch,
        )
        rsps.add(
            responses.GET,
            f"{EUTILS_BASE_URL}esummary.fcgi",
            json=empty_esummary,
        )
        result = search_related_papers(criteria)

    assert result.candidates == []
    assert len(result.source_runs) == 1
    run = result.source_runs[0]
    assert run.source_id == "pubmed"
    assert run.status == SourceRunStatus.empty
    assert run.hit_count == 0
    assert run.error is None


def test_fail_soft_keeps_other_sources_when_one_errors() -> None:
    criteria = SearchCriteria.model_validate(
        {
            "topic_analysis": {
                "facets": [
                    {"id": "s1", "label": "S1", "concepts": ["x"], "retmax": 5}
                ]
            },
            "source_overrides": {},
        }
    )

    def boom(_criteria: SearchCriteria) -> list[PaperCandidate]:
        raise RuntimeError("rate limited")

    surviving = PaperCandidate.model_validate(
        {
            "source_id": "stub",
            "source_uid": "99",
            "doi": None,
            "title": "Stub hit",
            "authors": [],
            "journal": None,
            "published_year": 2020,
            "url": "https://example.test/99",
            "snippet": None,
            "facet_id": "s1",
            "raw_payload_ref": None,
        }
    )

    def stub_ok(_criteria: SearchCriteria) -> list[PaperCandidate]:
        return [surviving]

    result = search_related_papers(
        criteria,
        registry={"pubmed": boom, "stub": stub_ok},
    )

    assert result.candidates == [surviving]
    assert len(result.source_runs) == 2

    by_id = {run.source_id: run for run in result.source_runs}
    assert by_id["pubmed"].status == SourceRunStatus.error
    assert by_id["pubmed"].error is not None
    assert "rate limited" in by_id["pubmed"].error
    assert by_id["pubmed"].hit_count == 0
    assert by_id["stub"].status == SourceRunStatus.ok
    assert by_id["stub"].hit_count == 1


def test_orchestrate_dedupes_across_sources() -> None:
    criteria = SearchCriteria.model_validate(
        {
            "topic_analysis": {
                "facets": [
                    {"id": "s1", "label": "S1", "concepts": ["x"], "retmax": 5}
                ]
            },
            "source_overrides": {},
        }
    )
    shared_doi = "10.1038/s41586-022-05543-x"
    a = PaperCandidate.model_validate(
        {
            "source_id": "pubmed",
            "source_uid": "1",
            "doi": shared_doi,
            "title": "First",
            "authors": [],
            "journal": None,
            "published_year": 2022,
            "url": "https://pubmed.ncbi.nlm.nih.gov/1/",
            "snippet": None,
            "facet_id": "s1",
            "raw_payload_ref": None,
        }
    )
    b = PaperCandidate.model_validate(
        {
            "source_id": "stub",
            "source_uid": "2",
            "doi": shared_doi.upper(),
            "title": "Duplicate DOI",
            "authors": [],
            "journal": None,
            "published_year": 2022,
            "url": "https://example.test/2",
            "snippet": None,
            "facet_id": "s1",
            "raw_payload_ref": None,
        }
    )

    result = search_related_papers(
        criteria,
        registry={
            "pubmed": lambda _c: [a],
            "stub": lambda _c: [b],
        },
    )

    assert result.candidates == [a]
    assert all(run.status == SourceRunStatus.ok for run in result.source_runs)
