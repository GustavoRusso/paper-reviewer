"""Confirm retrieval triage: pass through all search candidates."""

from __future__ import annotations

from paper_reviewer.schemas.topic_brief_generation.related_paper_search import (
    RelatedPaperSearchResult,
)
from paper_reviewer.schemas.topic_brief_generation.retrieval_triage import (
    RetrievalTriageResult,
)


def confirm_retrieval_triage(
    search_result: RelatedPaperSearchResult,
) -> RetrievalTriageResult:
    """Retain every search candidate (v1 pass-through). Caller owns UI timestamp."""
    return RetrievalTriageResult(
        retained=list(search_result.candidates),
        rejected=[],
        confirmed_at=None,
    )
