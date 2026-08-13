"""PMC Cloud enrichment helper (updated AWS Open Data layout)."""

from __future__ import annotations

from typing import Any, Callable
from urllib.parse import urlparse, urlunparse
from xml.etree import ElementTree as ET

import requests

PMC_CLOUD_BUCKET = "pmc-oa-opendata"
PMC_CLOUD_HTTPS_BASE = f"https://{PMC_CLOUD_BUCKET}.s3.amazonaws.com"
PMC_ARTICLE_URL_TEMPLATE = "https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"

HttpGet = Callable[..., Any]


def normalize_pmcid(value: str) -> str:
    """Return PMCID with a ``PMC`` prefix."""
    stripped = value.strip()
    if stripped.upper().startswith("PMC"):
        return f"PMC{stripped[3:]}"
    return f"PMC{stripped}"


def s3_url_to_https(url: str) -> str:
    """Convert ``s3://pmc-oa-opendata/...`` to a stable HTTPS object URL.

    Strips ephemeral query params such as ``md5``.
    """
    parsed = urlparse(url.strip())
    if parsed.scheme == "s3":
        key = parsed.path.lstrip("/")
        return f"{PMC_CLOUD_HTTPS_BASE}/{key}"
    if parsed.scheme in {"http", "https"}:
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    return url


def fetch_pmc_cloud_enrichment(
    pmcid: str | None,
    *,
    http_get: HttpGet | None = None,
) -> dict[str, Any]:
    """Fetch PMC Cloud enrichment fields for one PMCID.

    Returns a dict suitable for merging into an inform payload, or ``{}`` when
    Cloud has no article version / no body text. Raises on HTTP or parse errors.
    """
    get = http_get or requests.get
    if not pmcid or not str(pmcid).strip():
        return {}
    return _fetch_enrichment(normalize_pmcid(str(pmcid)), get)


def _fetch_enrichment(pmcid: str, get: HttpGet) -> dict[str, Any]:
    version = _highest_version(pmcid, get)
    if version is None:
        return {}

    meta = _load_metadata(pmcid, version, get)

    result: dict[str, Any] = {
        "pmcid": pmcid,
        "pmcid_version": version,
        "is_open_access": meta.get("is_pmc_openaccess"),
        "pmc_article_url": PMC_ARTICLE_URL_TEMPLATE.format(pmcid=pmcid),
    }

    text_url = meta.get("text_url")
    if text_url:
        text_body = _download_text(str(text_url), get)
        if text_body:
            result["full_text_plain"] = text_body

    pdf_url = meta.get("pdf_url")
    if pdf_url:
        result["open_access_pdf_url"] = s3_url_to_https(str(pdf_url))

    return result


def _checked_get(get: HttpGet, url: str, **kwargs: Any) -> Any:
    response = get(url, **kwargs)
    response.raise_for_status()
    return response


def _highest_version(pmcid: str, get: HttpGet) -> int | None:
    response = _checked_get(
        get,
        PMC_CLOUD_HTTPS_BASE + "/",
        params={"list-type": "2", "prefix": f"{pmcid}.", "delimiter": "/"},
        timeout=60,
    )

    root = ET.fromstring(response.text)
    versions: list[int] = []
    for prefix_el in root.findall(".//{*}CommonPrefixes/{*}Prefix"):
        text = (prefix_el.text or "").strip().rstrip("/")
        # Expect PMC{id}.{version}
        if not text.startswith(f"{pmcid}."):
            continue
        suffix = text[len(pmcid) + 1 :]
        if suffix.isdigit():
            versions.append(int(suffix))
    if not versions:
        return None
    return max(versions)


def _load_metadata(pmcid: str, version: int, get: HttpGet) -> dict[str, Any]:
    url = f"{PMC_CLOUD_HTTPS_BASE}/metadata/{pmcid}.{version}.json"
    response = _checked_get(get, url, timeout=60)
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError(f"PMC Cloud metadata for {pmcid}.{version} is not an object")
    return data


def _download_text(text_url: str, get: HttpGet) -> str | None:
    https_url = s3_url_to_https(text_url)
    response = _checked_get(get, https_url, timeout=120)
    body = response.text
    return body if body.strip() else None
