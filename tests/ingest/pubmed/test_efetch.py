"""PubMed EFetch HTTP helper."""

from __future__ import annotations

import responses

from paper_reviewer.ingest.pubmed.config import EUTILS_BASE_URL
from paper_reviewer.ingest.pubmed.efetch import fetch_pubmed_efetch_xml


@responses.activate
def test_fetch_pubmed_efetch_xml_one_pmid() -> None:
    responses.add(
        responses.GET,
        f"{EUTILS_BASE_URL}efetch.fcgi",
        body="<PubmedArticleSet></PubmedArticleSet>",
        status=200,
        content_type="application/xml",
        match=[
            responses.matchers.query_param_matcher(
                {"db": "pubmed", "id": "123", "retmode": "xml", "api_key": "k"},
                strict_match=False,
            )
        ],
    )

    xml = fetch_pubmed_efetch_xml("123", api_key="k")

    assert "PubmedArticleSet" in xml
    assert len(responses.calls) == 1


@responses.activate
def test_fetch_pubmed_efetch_xml_raises_on_http_error() -> None:
    responses.add(
        responses.GET,
        f"{EUTILS_BASE_URL}efetch.fcgi",
        body="rate limit",
        status=429,
    )

    try:
        fetch_pubmed_efetch_xml("123")
    except RuntimeError as exc:
        assert "429" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
