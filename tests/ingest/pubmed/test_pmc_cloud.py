"""PMC Cloud enrichment helper (stubbed HTTP)."""

from __future__ import annotations

import json

import pytest
import responses
import requests

from paper_reviewer.ingest.pubmed.pmc_cloud import (
    PMC_CLOUD_HTTPS_BASE,
    fetch_pmc_cloud_enrichment,
    normalize_pmcid,
    s3_url_to_https,
    usable_full_text_plain,
)

_LIST_URL = PMC_CLOUD_HTTPS_BASE + "/"


def _list_bucket_xml(*prefixes: str) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">',
        "<Name>pmc-oa-opendata</Name>",
        "<Prefix>PMC11370360.</Prefix>",
        "<Delimiter>/</Delimiter>",
    ]
    for prefix in prefixes:
        parts.append(f"<CommonPrefixes><Prefix>{prefix}</Prefix></CommonPrefixes>")
    parts.append("</ListBucketResult>")
    return "".join(parts)


def _meta(
    *,
    pmcid: str = "PMC11370360",
    version: int = 2,
    is_oa: bool = True,
    is_manuscript: bool = False,
    text: bool = True,
    pdf: bool = True,
) -> dict:
    data: dict = {
        "pmcid": pmcid,
        "version": version,
        "is_pmc_openaccess": is_oa,
        "is_manuscript": is_manuscript,
        "license_code": "CC BY" if is_oa else "TDM",
    }
    if text:
        data["text_url"] = (
            f"s3://pmc-oa-opendata/{pmcid}.{version}/{pmcid}.{version}.txt"
            f"?md5=abc123"
        )
    if pdf:
        data["pdf_url"] = (
            f"s3://pmc-oa-opendata/{pmcid}.{version}/{pmcid}.{version}.pdf"
            f"?md5=def456"
        )
    return data


def test_normalize_pmcid() -> None:
    assert normalize_pmcid("11370360") == "PMC11370360"
    assert normalize_pmcid("PMC11370360") == "PMC11370360"
    assert normalize_pmcid(" pmc11370360 ") == "PMC11370360"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        ("   ", None),
        ("  \n\t", None),
        ("Full article.", "Full article."),
        ("\nFull article.", "\nFull article."),
    ],
)
def test_usable_full_text_plain(value: str | None, expected: str | None) -> None:
    assert usable_full_text_plain(value) == expected


def _stub_article_with_txt(
    *,
    pmcid: str,
    version: int,
    txt_body: str = "",
    txt_status: int = 200,
    pdf: bool = False,
) -> None:
    responses.add(
        responses.GET,
        _LIST_URL,
        body=_list_bucket_xml(f"{pmcid}.{version}/"),
        status=200,
        content_type="application/xml",
    )
    responses.add(
        responses.GET,
        f"{PMC_CLOUD_HTTPS_BASE}/metadata/{pmcid}.{version}.json",
        body=json.dumps(_meta(pmcid=pmcid, version=version, pdf=pdf)),
        status=200,
        content_type="application/json",
    )
    responses.add(
        responses.GET,
        f"{PMC_CLOUD_HTTPS_BASE}/{pmcid}.{version}/{pmcid}.{version}.txt",
        body=txt_body,
        status=txt_status,
        content_type="text/plain",
    )


def test_s3_url_to_https_strips_md5() -> None:
    assert s3_url_to_https(
        "s3://pmc-oa-opendata/PMC11370360.2/PMC11370360.2.pdf?md5=abc"
    ) == f"{PMC_CLOUD_HTTPS_BASE}/PMC11370360.2/PMC11370360.2.pdf"


@responses.activate
def test_fetch_picks_highest_version_and_downloads_text() -> None:
    responses.add(
        responses.GET,
        _LIST_URL,
        body=_list_bucket_xml("PMC11370360.1/", "PMC11370360.2/"),
        status=200,
        content_type="application/xml",
        match=[
            responses.matchers.query_param_matcher(
                {"list-type": "2", "prefix": "PMC11370360.", "delimiter": "/"},
                strict_match=False,
            )
        ],
    )
    responses.add(
        responses.GET,
        f"{PMC_CLOUD_HTTPS_BASE}/metadata/PMC11370360.2.json",
        body=json.dumps(_meta()),
        status=200,
        content_type="application/json",
    )
    responses.add(
        responses.GET,
        f"{PMC_CLOUD_HTTPS_BASE}/PMC11370360.2/PMC11370360.2.txt",
        body="Full article plain text.",
        status=200,
        content_type="text/plain",
    )

    result = fetch_pmc_cloud_enrichment("PMC11370360")

    assert result["pmcid"] == "PMC11370360"
    assert result["pmcid_version"] == 2
    assert result["is_open_access"] is True
    assert result["full_text_plain"] == "Full article plain text."
    assert result["open_access_pdf_url"] == (
        f"{PMC_CLOUD_HTTPS_BASE}/PMC11370360.2/PMC11370360.2.pdf"
    )
    assert result["pmc_article_url"] == (
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC11370360/"
    )


@responses.activate
def test_fetch_author_manuscript_not_oa_still_stores_text() -> None:
    responses.add(
        responses.GET,
        _LIST_URL,
        body=_list_bucket_xml("PMC5334499.1/"),
        status=200,
        content_type="application/xml",
    )
    responses.add(
        responses.GET,
        f"{PMC_CLOUD_HTTPS_BASE}/metadata/PMC5334499.1.json",
        body=json.dumps(
            _meta(
                pmcid="PMC5334499",
                version=1,
                is_oa=False,
                is_manuscript=True,
                pdf=False,
            )
        ),
        status=200,
        content_type="application/json",
    )
    responses.add(
        responses.GET,
        f"{PMC_CLOUD_HTTPS_BASE}/PMC5334499.1/PMC5334499.1.txt",
        body="Author manuscript text.",
        status=200,
        content_type="text/plain",
    )

    result = fetch_pmc_cloud_enrichment("5334499")

    assert result["pmcid"] == "PMC5334499"
    assert result["pmcid_version"] == 1
    assert result["is_open_access"] is False
    assert result["full_text_plain"] == "Author manuscript text."
    assert "open_access_pdf_url" not in result


@responses.activate
def test_fetch_text_without_pdf() -> None:
    responses.add(
        responses.GET,
        _LIST_URL,
        body=_list_bucket_xml("PMC1.1/"),
        status=200,
        content_type="application/xml",
    )
    responses.add(
        responses.GET,
        f"{PMC_CLOUD_HTTPS_BASE}/metadata/PMC1.1.json",
        body=json.dumps(_meta(pmcid="PMC1", version=1, pdf=False)),
        status=200,
        content_type="application/json",
    )
    responses.add(
        responses.GET,
        f"{PMC_CLOUD_HTTPS_BASE}/PMC1.1/PMC1.1.txt",
        body="Text only.",
        status=200,
        content_type="text/plain",
    )

    result = fetch_pmc_cloud_enrichment("PMC1")

    assert result["full_text_plain"] == "Text only."
    assert "open_access_pdf_url" not in result


@responses.activate
@pytest.mark.parametrize("txt_body", ["", "  \n\t"])
def test_fetch_blank_txt_omits_full_text_plain(txt_body: str) -> None:
    _stub_article_with_txt(pmcid="PMC1", version=1, txt_body=txt_body)

    result = fetch_pmc_cloud_enrichment("PMC1")

    assert "full_text_plain" not in result
    assert result["pmcid"] == "PMC1"
    assert result["pmcid_version"] == 1


@responses.activate
def test_fetch_preserves_leading_newline_in_body() -> None:
    body = "\nFull article plain text."
    _stub_article_with_txt(pmcid="PMC1", version=1, txt_body=body)

    result = fetch_pmc_cloud_enrichment("PMC1")

    assert result["full_text_plain"] == body


@responses.activate
def test_fetch_txt_http_error_raises() -> None:
    _stub_article_with_txt(pmcid="PMC11370360", version=1, txt_status=404)

    with pytest.raises(requests.HTTPError):
        fetch_pmc_cloud_enrichment("PMC11370360")


@responses.activate
def test_fetch_no_versions_returns_empty() -> None:
    responses.add(
        responses.GET,
        _LIST_URL,
        body=_list_bucket_xml(),
        status=200,
        content_type="application/xml",
    )

    assert fetch_pmc_cloud_enrichment("PMC999") == {}


@responses.activate
def test_fetch_list_http_error_raises() -> None:
    responses.add(responses.GET, _LIST_URL, body="boom", status=500)

    with pytest.raises(requests.HTTPError):
        fetch_pmc_cloud_enrichment("PMC11370360")


@responses.activate
def test_fetch_metadata_http_error_raises() -> None:
    responses.add(
        responses.GET,
        _LIST_URL,
        body=_list_bucket_xml("PMC11370360.1/"),
        status=200,
        content_type="application/xml",
    )
    responses.add(
        responses.GET,
        f"{PMC_CLOUD_HTTPS_BASE}/metadata/PMC11370360.1.json",
        body="missing",
        status=404,
    )

    with pytest.raises(requests.HTTPError):
        fetch_pmc_cloud_enrichment("PMC11370360")


def test_fetch_empty_pmcid_returns_empty() -> None:
    assert fetch_pmc_cloud_enrichment(None) == {}
    assert fetch_pmc_cloud_enrichment("") == {}
    assert fetch_pmc_cloud_enrichment("   ") == {}
