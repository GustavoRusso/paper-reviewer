"""Merge and dedupe PaperCandidate lists for related-paper search."""

from __future__ import annotations

from paper_reviewer.schemas.topic_brief_generation.related_paper_search import (
    PaperCandidate,
)


def _dedupe_key(candidate: PaperCandidate) -> tuple[str, ...]:
    if candidate.doi:
        return ("doi", candidate.doi.casefold())
    return ("source", candidate.source_id, candidate.source_uid)


def merge_candidates(candidates: list[PaperCandidate]) -> list[PaperCandidate]:
    """Dedupe candidates: DOI (case-normalized) when present, else (source_id, source_uid).

    Keeps the first occurrence of each identity key; preserves input order.
    """
    seen: set[tuple[str, ...]] = set()
    merged: list[PaperCandidate] = []
    for candidate in candidates:
        key = _dedupe_key(candidate)
        if key in seen:
            continue
        seen.add(key)
        merged.append(candidate)
    return merged
