"""Merge and dedupe PaperCandidate lists for search external sources."""

from __future__ import annotations

from paper_reviewer.schemas.topic_scope.search_external_sources import (
    PaperCandidate,
)


def _normalized_doi(candidate: PaperCandidate) -> str | None:
    if candidate.doi is None:
        return None
    text = str(candidate.doi).strip()
    if not text:
        return None
    return text.upper()


def _sort_key(candidate: PaperCandidate) -> tuple[bool, int, bool, int, str]:
    """Newest year then date first; null year/date last; tie-break on uppercase DOI."""
    year = candidate.published_year
    pub = candidate.pub_date
    doi = candidate.doi or ""
    return (
        year is None,
        -(year or 0),
        pub is None,
        -(pub.toordinal()) if pub is not None else 0,
        doi,
    )


def merge_candidates(candidates: list[PaperCandidate]) -> list[PaperCandidate]:
    """Drop missing/blank DOI hits; dedupe by uppercase DOI; sort newest year/date first.

    Kept candidates always have a non-blank uppercase ``doi``.
    """
    seen: set[str] = set()
    merged: list[PaperCandidate] = []
    for candidate in candidates:
        doi = _normalized_doi(candidate)
        if doi is None:
            continue
        if doi in seen:
            continue
        seen.add(doi)
        merged.append(candidate.model_copy(update={"doi": doi}))
    merged.sort(key=_sort_key)
    return merged
