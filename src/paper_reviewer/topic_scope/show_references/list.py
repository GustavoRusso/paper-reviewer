"""List Papers already selected as References for a Topic scope."""

from __future__ import annotations

from sqlalchemy.orm import Session

from paper_reviewer.models.paper import Paper
from paper_reviewer.models.topic_scope import TopicScope
from paper_reviewer.models.topic_scope.reference import (
    Reference,
    list_references_for_scope,
)
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.show_references import (
    ReferencedPaper,
    ShowReferencesResult,
)


def _paper_brief_available(paper: Paper) -> bool:
    brief = paper.paper_brief
    return brief is not None and brief.status == PaperAspectStatus.succeeded


def _to_referenced_paper(row: Reference, paper: Paper) -> ReferencedPaper:
    return ReferencedPaper(
        title=paper.title,
        url=paper.url,
        doi=paper.doi,
        authors=list(paper.authors),
        journal=paper.journal,
        published_year=paper.published_year,
        referenced_at=row.created_at,
        paper_brief_available=_paper_brief_available(paper),
    )


def list_show_references(
    session: Session,
    topic_scope: TopicScope,
) -> ShowReferencesResult:
    """Return bibliographic cards for References on ``topic_scope``."""
    pairs = list_references_for_scope(session, topic_scope.id)
    return ShowReferencesResult(
        papers=[_to_referenced_paper(row, paper) for row, paper in pairs]
    )
