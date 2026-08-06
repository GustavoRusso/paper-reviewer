"""PubMed RESTAPIConfig builder: shape and stubbed E-utilities HTTP."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse

import responses
from dlt.sources.rest_api import rest_api_resources

import pytest

from paper_reviewer.ingest.pubmed.config import (
    EUTILS_BASE_URL,
    _flatten_esummary_docsums,
    build_pubmed_rest_api_config,
)

ESEARCH_JSON = {
    "header": {"type": "esearch", "version": "0.3"},
    "esearchresult": {
        "count": "2",
        "retmax": "2",
        "retstart": "0",
        "querykey": "1",
        "webenv": "MCID_TEST_HISTORY",
        "idlist": ["21256409", "20956156"],
        "translationset": [],
        "querytranslation": "asthma[MeSH Terms]",
    },
}

ESUMMARY_JSON = {
    "header": {"type": "esummary", "version": "0.3"},
    "result": {
        "uids": ["21256409", "20956156"],
        "21256409": {
            "uid": "21256409",
            "pubdate": "2011 Feb",
            "epubdate": "2009 Dec 4",
            "source": "J Pediatr Nurs",
            "authors": [{"name": "Hines AB", "authtype": "Author", "clusterid": ""}],
            "title": (
                "Asthma: a health disparity among African American children: "
                "the impact and implications for pediatric nurses."
            ),
            "fulljournalname": "Journal of pediatric nursing",
            "articleids": [
                {"idtype": "pubmed", "idtypen": 1, "value": "21256409"},
                {"idtype": "doi", "idtypen": 3, "value": "10.1016/j.pedn.2009.10.006"},
            ],
            "attributes": ["Has Abstract"],
        },
        "20956156": {
            "uid": "20956156",
            "pubdate": "2009 Dec",
            "epubdate": "",
            "source": "Eur Respir Rev",
            "authors": [
                {"name": "Irfan M", "authtype": "Author", "clusterid": ""},
                {"name": "Munavvar M", "authtype": "Author", "clusterid": ""},
            ],
            "title": "An unusual cause of haemoptysis in a patient with asthma.",
            "fulljournalname": (
                "European respiratory review : an official journal of the "
                "European Respiratory Society"
            ),
            "articleids": [
                {"idtype": "pubmed", "idtypen": 1, "value": "20956156"},
                {"idtype": "doi", "idtypen": 3, "value": "10.1183/09059180.00003009"},
            ],
            "attributes": [],
        },
    },
}


def _resource_by_name(config: dict[str, Any], name: str) -> dict[str, Any]:
    for resource in config["resources"]:
        if resource["name"] == name:
            return resource
    raise AssertionError(f"resource {name!r} missing")


def test_config_targets_eutils_esearch_then_esummary() -> None:
    term = 'asthma[mesh] AND leukotrienes[mesh] AND 2009[pdat]'
    config = build_pubmed_rest_api_config(term=term, retmax=10, sort="relevance")

    assert config["client"]["base_url"] == EUTILS_BASE_URL

    esearch = _resource_by_name(config, "esearch")
    assert esearch["endpoint"]["path"] == "esearch.fcgi"
    params = esearch["endpoint"]["params"]
    assert params["db"] == "pubmed"
    assert params["retmode"] == "json"
    assert params["usehistory"] == "y"
    assert params["term"] == term
    assert params["retmax"] == 10
    assert params["sort"] == "relevance"

    esummary = _resource_by_name(config, "esummary")
    assert esummary["endpoint"]["path"] == "esummary.fcgi"
    child_params = esummary["endpoint"]["params"]
    assert child_params["db"] == "pubmed"
    assert child_params["retmode"] == "json"
    assert child_params["WebEnv"] == "{resources.esearch.webenv}"
    assert child_params["query_key"] == "{resources.esearch.querykey}"
    assert child_params["retmax"] == 10


def test_esummary_retmax_defaults_to_20_when_caller_omits_retmax() -> None:
    config = build_pubmed_rest_api_config(term="CRISPR")
    esearch = _resource_by_name(config, "esearch")
    assert "retmax" not in esearch["endpoint"]["params"]
    esummary = _resource_by_name(config, "esummary")
    assert esummary["endpoint"]["params"]["retmax"] == 20


def test_esummary_retmax_capped_at_500_for_json() -> None:
    config = build_pubmed_rest_api_config(term="CRISPR", retmax=1000)
    esearch = _resource_by_name(config, "esearch")
    assert esearch["endpoint"]["params"]["retmax"] == 1000
    esummary = _resource_by_name(config, "esummary")
    assert esummary["endpoint"]["params"]["retmax"] == 500


def test_flatten_esummary_raises_on_ncbi_json_error() -> None:
    class _FakeResponse:
        def json(self) -> dict[str, Any]:
            return {
                "error": (
                    "Too many UIDs in request. "
                    "Maximum number of UIDs is 500 for JSON format output."
                )
            }

    with pytest.raises(RuntimeError, match="Too many UIDs"):
        _flatten_esummary_docsums(_FakeResponse())


def test_config_includes_api_key_in_query_when_provided() -> None:
    config = build_pubmed_rest_api_config(term="CRISPR", api_key="TESTKEY")
    auth = config["client"]["auth"]
    assert auth["type"] == "api_key"
    assert auth["name"] == "api_key"
    assert auth["api_key"] == "TESTKEY"
    assert auth["location"] == "query"


def test_config_omits_auth_when_api_key_absent() -> None:
    config = build_pubmed_rest_api_config(term="CRISPR")
    assert "auth" not in config["client"]


def test_stubbed_http_yields_real_shaped_docsums_via_history() -> None:
    config = build_pubmed_rest_api_config(
        term="asthma[mesh] AND 2009[pdat]",
        retmax=2,
        api_key="TESTKEY",
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

        docsums: list[dict[str, Any]] = []
        for resource in rest_api_resources(config):
            if resource.name == "esummary":
                docsums.extend(list(resource))

        assert [row["uid"] for row in docsums] == ["21256409", "20956156"]
        assert "Asthma" in docsums[0]["title"]
        assert docsums[0]["articleids"][1]["value"] == "10.1016/j.pedn.2009.10.006"

        esearch_urls = [
            call.request.url
            for call in rsps.calls
            if call.request.url and "esearch.fcgi" in call.request.url
        ]
        esummary_urls = [
            call.request.url
            for call in rsps.calls
            if call.request.url and "esummary.fcgi" in call.request.url
        ]
        assert esearch_urls
        assert esummary_urls

        esearch_qs = parse_qs(urlparse(esearch_urls[0]).query)
        assert esearch_qs["db"] == ["pubmed"]
        assert esearch_qs["usehistory"] == ["y"]
        assert esearch_qs["retmode"] == ["json"]
        assert esearch_qs["api_key"] == ["TESTKEY"]
        assert esearch_qs["term"] == ["asthma[mesh] AND 2009[pdat]"]

        esummary_qs = parse_qs(urlparse(esummary_urls[0]).query)
        assert esummary_qs["WebEnv"] == ["MCID_TEST_HISTORY"]
        assert esummary_qs["query_key"] == ["1"]
        assert esummary_qs["api_key"] == ["TESTKEY"]
        assert esummary_qs["retmax"] == ["2"]
