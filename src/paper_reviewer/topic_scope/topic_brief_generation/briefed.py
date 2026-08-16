"""Count References that already have a succeeded paper brief."""

from __future__ import annotations

from sqlalchemy.orm import Session

from paper_reviewer.models.topic_scope.reference import list_references_for_scope
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)


def count_briefed_references(session: Session, topic_scope_id: int) -> int:
    """Return how many References on the scope have a succeeded PaperBrief."""
    pairs = list_references_for_scope(session, topic_scope_id)
    return sum(
        1
        for _ref, paper in pairs
        if paper.paper_brief is not None
        and paper.paper_brief.status is PaperAspectStatus.succeeded
    )
