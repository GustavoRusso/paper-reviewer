"""PubMed @dlt.source end-to-end for one facet (faked HTTP)."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import responses

from paper_reviewer.ingest.pubmed.config import EUTILS_BASE_URL
from paper_reviewer.ingest.pubmed.source import pubmed
from paper_reviewer.schemas.topic_brief_generation.related_paper_search import (
    PaperCandidate,
    PubMedFacetOverride,
)
from paper_reviewer.schemas.topic_brief_generation.topic_analysis import TopicFacet
from tests.ingest.pubmed.test_config import ESEARCH_JSON, ESUMMARY_JSON

EMPTY_ESEARCH_JSON = {
    "header": {"type": "esearch", "version": "0.3"},
    "esearchresult": {
        "count": "0",
        "retmax": "0",
        "retstart": "0",
        "querykey": "1",
        "webenv": "MCID_EMPTY_HISTORY",
        "idlist": [],
        "translationset": [],
        "querytranslation": "nosuchterm[MeSH Terms]",
    },
}

EMPTY_ESUMMARY_JSON = {
    "header": {"type": "esummary", "version": "0.3"},
    "result": {"uids": []},
}


def _fixture_facet() -> TopicFacet:
    return TopicFacet.model_validate(
        {
            "id": "fixture-pubmed",
            "label": "Fixture PubMed",
            "concepts": ["asthma", "leukotrienes"],
            "retmax": 10,
        }
    )


def _fixture_override() -> PubMedFacetOverride:
    return PubMedFacetOverride.model_validate(
        {
            "raw_term": "asthma[mesh] AND leukotrienes[mesh] AND 2009[pdat]",
        }
    )


def _collect_candidates(source) -> list[PaperCandidate]:
    rows = list(source.candidates)
    return [
        row if isinstance(row, PaperCandidate) else PaperCandidate.model_validate(row)
        for row in rows
    ]


def test_pubmed_source_yields_candidates_for_one_facet() -> None:
    facet = _fixture_facet()
    override = _fixture_override()

    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
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

        candidates = _collect_candidates(
            pubmed(facet, override=override, api_key="TESTKEY")
        )

        assert [c.source_uid for c in candidates] == ["21256409", "20956156"]
        assert all(c.source_id == "pubmed" for c in candidates)
        assert all(c.facet_id == "fixture-pubmed" for c in candidates)

        first = candidates[0]
        assert first.doi == "10.1016/j.pedn.2009.10.006"
        assert "Asthma" in first.title
        assert first.authors == ["Hines AB"]
        assert first.journal == "Journal of pediatric nursing"
        assert first.published_year == 2011
        assert first.url == "https://pubmed.ncbi.nlm.nih.gov/21256409/"

        esearch_urls = [
            call.request.url
            for call in rsps.calls
            if call.request.url and "esearch.fcgi" in call.request.url
        ]
        assert esearch_urls
        esearch_qs = parse_qs(urlparse(esearch_urls[0]).query)
        assert esearch_qs["term"] == [
            "asthma[mesh] AND leukotrienes[mesh] AND 2009[pdat]"
        ]
        assert esearch_qs["retmax"] == ["10"]
        assert esearch_qs["api_key"] == ["TESTKEY"]


def test_pubmed_source_structured_facet_compiles_term() -> None:
    facet = TopicFacet.model_validate(
        {
            "id": "core-concepts",
            "label": "Core concepts",
            "concepts": ["glioblastoma", "immunotherapy"],
            "synonyms": ["GBM"],
            "date_from": "2018-01-01",
            "retmax": 5,
        }
    )

    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
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

        candidates = _collect_candidates(pubmed(facet))

        assert len(candidates) == 2
        assert candidates[0].facet_id == "core-concepts"

        esearch_urls = [
            call.request.url
            for call in rsps.calls
            if call.request.url and "esearch.fcgi" in call.request.url
        ]
        esearch_qs = parse_qs(urlparse(esearch_urls[0]).query)
        term = esearch_qs["term"][0]
        assert "glioblastoma" in term
        assert "immunotherapy" in term
        assert "GBM" in term
        assert "AND" in term
        assert "OR" in term
        assert esearch_qs["retmax"] == ["5"]


def test_pubmed_source_zero_hits_yields_no_candidates() -> None:
    facet = _fixture_facet()
    override = PubMedFacetOverride(raw_term="nosuchterm[mesh]")

    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            responses.GET,
            f"{EUTILS_BASE_URL}esearch.fcgi",
            json=EMPTY_ESEARCH_JSON,
        )
        rsps.add(
            responses.GET,
            f"{EUTILS_BASE_URL}esummary.fcgi",
            json=EMPTY_ESUMMARY_JSON,
        )

        candidates = _collect_candidates(pubmed(facet, override=override))

    assert candidates == []
