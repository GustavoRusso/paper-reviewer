"""Load a succeeded global PaperBrief for the reader page."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from paper_reviewer.models.paper import get_paper_by_doi
from paper_reviewer.models.paper_brief import PaperBrief, get_paper_brief_by_paper_id
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    PaperBriefContent,
)
from paper_reviewer.schemas.topic_scope.paper_brief import (
    PaperBriefRead,
    PaperBriefReadStatus,
)


def _evaluation_score_for_read(brief: PaperBrief) -> Decimal | None:
    if (
        brief.evaluation_status == PaperAspectStatus.succeeded
        and brief.evaluation_score is not None
    ):
        return brief.evaluation_score
    return None


def load_paper_brief_for_read(session: Session, doi: str) -> PaperBriefRead:
    """Return bibliographic fields and content for a succeeded paper brief."""
    paper = get_paper_by_doi(session, doi)
    if paper is None:
        return PaperBriefRead(
            status=PaperBriefReadStatus.paper_missing,
            doi=doi,
        )

    bibliographic = {
        "doi": paper.doi,
        "title": paper.title,
        "url": paper.url,
        "authors": list(paper.authors),
        "journal": paper.journal,
        "published_year": paper.published_year,
    }
    brief = get_paper_brief_by_paper_id(session, paper.id)
    if brief is None or brief.status != PaperAspectStatus.succeeded:
        return PaperBriefRead(
            status=PaperBriefReadStatus.brief_unavailable,
            **bibliographic,
        )
    evaluation_score = _evaluation_score_for_read(brief)
    if brief.content is None:
        return PaperBriefRead(
            status=PaperBriefReadStatus.invalid_content,
            evaluation_score=evaluation_score,
            **bibliographic,
        )
    try:
        content = PaperBriefContent.model_validate(brief.content)
    except Exception:
        return PaperBriefRead(
            status=PaperBriefReadStatus.invalid_content,
            evaluation_score=evaluation_score,
            **bibliographic,
        )
    return PaperBriefRead(
        status=PaperBriefReadStatus.ready,
        content=content,
        evaluation_score=evaluation_score,
        **bibliographic,
    )
