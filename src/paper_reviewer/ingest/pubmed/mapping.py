"""Map PubMed ESummary DocSums to PaperCandidate."""

from __future__ import annotations

from datetime import date
from typing import Any

from paper_reviewer.schemas.topic_scope.search_external_sources import (
    PaperCandidate,
)

_PUBMED_SOURCE_ID = "pubmed"
_PUBMED_URL_TEMPLATE = "https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
_MONTH_BY_ABBR: dict[str, int] = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def docsum_to_candidate(docsum: dict[str, Any], *, facet_id: str) -> PaperCandidate:
    """Map one ESummary DocSum (JSON object) to a PaperCandidate."""
    pmid = str(docsum["uid"])
    return PaperCandidate(
        source_id=_PUBMED_SOURCE_ID,
        source_uid=pmid,
        doi=_doi_from_articleids(docsum.get("articleids")),
        title=str(docsum.get("title") or ""),
        authors=_author_names(docsum.get("authors")),
        journal=_journal_name(docsum),
        published_year=_published_year(docsum),
        pub_date=_pub_date(docsum),
        url=_PUBMED_URL_TEMPLATE.format(pmid=pmid),
        snippet=_usable_snippet(docsum.get("snippet")),
        facet_id=facet_id,
    )


def _doi_from_articleids(articleids: Any) -> str | None:
    if not isinstance(articleids, list):
        return None
    for entry in articleids:
        if not isinstance(entry, dict):
            continue
        if entry.get("idtype") == "doi":
            value = entry.get("value")
            if value is not None and str(value).strip():
                return str(value)
    return None


def _author_names(authors: Any) -> list[str]:
    if not isinstance(authors, list):
        return []
    names: list[str] = []
    for author in authors:
        if isinstance(author, dict) and author.get("name"):
            names.append(str(author["name"]))
    return names


def _journal_name(docsum: dict[str, Any]) -> str | None:
    full = docsum.get("fulljournalname")
    if full is not None and str(full).strip():
        return str(full)
    source = docsum.get("source")
    if source is not None and str(source).strip():
        return str(source)
    return None


def _published_year(docsum: dict[str, Any]) -> int | None:
    for key in ("pubdate", "epubdate"):
        year = _year_from_date_string(docsum.get(key))
        if year is not None:
            return year
    return None


def _pub_date(docsum: dict[str, Any]) -> date | None:
    for key in ("pubdate", "epubdate"):
        parsed = _full_date_from_docsum_string(docsum.get(key))
        if parsed is not None:
            return parsed
    return None


def _full_date_from_docsum_string(value: Any) -> date | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    parts = text.split()
    if len(parts) < 3:
        return None
    year_str, month_str, day_str = parts[0], parts[1], parts[2]
    if len(year_str) != 4 or not year_str.isdigit():
        return None
    month = _MONTH_BY_ABBR.get(month_str[:3].casefold())
    if month is None or not day_str.isdigit():
        return None
    try:
        return date(int(year_str), month, int(day_str))
    except ValueError:
        return None


def _year_from_date_string(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if len(text) < 4 or not text[:4].isdigit():
        return None
    return int(text[:4])


def _usable_snippet(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
