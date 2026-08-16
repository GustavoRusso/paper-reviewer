"""Briefed References for Topic brief generation (filter, order, citations)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from paper_reviewer.models.topic_scope.reference import list_references_for_scope
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)


@dataclass(frozen=True)
class BriefedReference:
    """One Reference that has a succeeded global PaperBrief."""

    reference_id: int
    created_at: datetime
    doi: str
    title: str
    pub_date: date | None
    citation_description: str
    paper_brief_content: dict[str, Any]


def citation_description(*, doi: str, title: str) -> str:
    """Build the app citation string: ``{DOI} — {title}`` (uppercase DOI)."""
    return f"{doi.upper()} — {title}"


def _is_briefed(paper: object) -> bool:
    brief = getattr(paper, "paper_brief", None)
    return brief is not None and brief.status is PaperAspectStatus.succeeded


def _sort_key(item: BriefedReference) -> tuple[bool, int, datetime, int]:
    """Newest pub_date first; null pub_date last; then created_at, id ascending."""
    pub = item.pub_date
    return (
        pub is None,
        -(pub.toordinal()) if pub is not None else 0,
        item.created_at,
        item.reference_id,
    )


def list_briefed_references(
    session: Session,
    topic_scope_id: int,
) -> list[BriefedReference]:
    """Return briefed References ordered for the topic-brief LLM payload."""
    items: list[BriefedReference] = []
    for ref, paper in list_references_for_scope(session, topic_scope_id):
        if not _is_briefed(paper):
            continue
        brief = paper.paper_brief
        assert brief is not None
        content = brief.content if isinstance(brief.content, dict) else {}
        items.append(
            BriefedReference(
                reference_id=ref.id,
                created_at=ref.created_at,
                doi=paper.doi,
                title=paper.title,
                pub_date=paper.pub_date,
                citation_description=citation_description(
                    doi=paper.doi,
                    title=paper.title,
                ),
                paper_brief_content=content,
            )
        )
    items.sort(key=_sort_key)
    return items


def count_briefed_references(session: Session, topic_scope_id: int) -> int:
    """Return how many References on the scope have a succeeded PaperBrief."""
    return len(list_briefed_references(session, topic_scope_id))
