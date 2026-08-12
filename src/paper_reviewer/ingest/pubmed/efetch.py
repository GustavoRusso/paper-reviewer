"""Fetch PubMed EFetch XML for one PMID (source-inform)."""

from __future__ import annotations

from typing import Any, Iterator

import dlt
import requests

from paper_reviewer.ingest.pubmed.config import EUTILS_BASE_URL
from paper_reviewer.ingest.pubmed.efetch_mapping import map_efetch_xml


def fetch_pubmed_efetch_xml(pmid: str, *, api_key: str | None = None) -> str:
    """GET EFetch XML for a single PubMed PMID."""
    params: dict[str, str] = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml",
    }
    if api_key:
        params["api_key"] = api_key
    response = requests.get(
        f"{EUTILS_BASE_URL}efetch.fcgi",
        params=params,
        timeout=60,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"HTTP {response.status_code} from NCBI EFetch: {response.text[:200]}"
        )
    return response.text


def fetch_pubmed_source_record(
    pmid: str,
    *,
    api_key: str | None = None,
) -> dict[str, Any]:
    """EFetch one PMID and return the mapped inform payload."""
    xml_text = fetch_pubmed_efetch_xml(pmid, api_key=api_key)
    return map_efetch_xml(xml_text)


@dlt.resource(name="efetch", write_disposition="replace")
def pubmed_efetch(
    pmid: str,
    *,
    api_key: str | None = None,
) -> Iterator[dict[str, Any]]:
    """dlt resource yielding one mapped EFetch row for ``pmid``."""
    yield fetch_pubmed_source_record(pmid, api_key=api_key)
