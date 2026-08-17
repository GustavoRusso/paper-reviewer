"""Load a succeeded global PaperBrief for the reader page."""

from __future__ import annotations

from sqlalchemy.orm import Session

from paper_reviewer.models.paper import get_paper_by_doi
from paper_reviewer.models.paper_brief import get_paper_brief_by_paper_id
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
    if brief.content is None:
        return PaperBriefRead(
            status=PaperBriefReadStatus.invalid_content,
            **bibliographic,
        )
    try:
        content = PaperBriefContent.model_validate(brief.content)
    except Exception:
        return PaperBriefRead(
            status=PaperBriefReadStatus.invalid_content,
            **bibliographic,
        )
    return PaperBriefRead(
        status=PaperBriefReadStatus.ready,
        content=content,
        **bibliographic,
    )
