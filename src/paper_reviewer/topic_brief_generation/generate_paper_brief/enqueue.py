"""Apply selection rules and submit brief jobs for archived papers."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from paper_reviewer.models.topic_brief_generation.paper import get_paper_by_id
from paper_reviewer.models.topic_brief_generation.paper_brief import (
    get_paper_brief_by_paper_id,
)
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_brief_generation.generate_paper_brief import (
    GeneratePaperBriefsEnqueueResult,
)


def needs_create_paper_brief(
    full_text_status: PaperAspectStatus,
    brief_status: PaperAspectStatus | None,
) -> bool:
    """Return True when page 7 should enqueue a brief for these statuses."""
    if full_text_status is not PaperAspectStatus.succeeded:
        return False
    return brief_status is None or brief_status is PaperAspectStatus.not_started


def enqueue_generate_paper_briefs(
    session: Session,
    paper_ids: list[int],
    *,
    submit_brief: Callable[[int, str], None],
) -> GeneratePaperBriefsEnqueueResult:
    """Select papers that need a brief and submit one job per selected id.

    Submits when full text is ``succeeded`` and the brief is missing or
    ``not_started``. Never passes ``force``.
    """
    submitted: list[int] = []
    skipped_terminal: list[int] = []

    for paper_id in paper_ids:
        paper = get_paper_by_id(session, paper_id)
        if paper is None:
            continue
        brief = get_paper_brief_by_paper_id(session, paper_id)
        brief_status = brief.status if brief is not None else None
        if needs_create_paper_brief(paper.full_text_status, brief_status):
            submit_brief(paper_id, paper.doi)
            submitted.append(paper_id)
            continue
        skipped_terminal.append(paper_id)

    return GeneratePaperBriefsEnqueueResult(
        submitted_paper_ids=submitted,
        skipped_already_terminal=skipped_terminal,
    )
