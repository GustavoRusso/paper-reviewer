"""Merge and dedupe PaperCandidate lists for search external sources."""

from __future__ import annotations

from paper_reviewer.schemas.topic_brief_generation.search_external_sources import (
    PaperCandidate,
)


def _normalized_doi(candidate: PaperCandidate) -> str | None:
    if candidate.doi is None:
        return None
    text = str(candidate.doi).strip()
    if not text:
        return None
    return text.upper()


def merge_candidates(candidates: list[PaperCandidate]) -> list[PaperCandidate]:
    """Drop missing/blank DOI hits; dedupe by uppercase DOI; keep first; preserve order.

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
    return merged
