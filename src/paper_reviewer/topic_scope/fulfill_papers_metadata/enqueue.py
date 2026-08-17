"""Apply selection rules and submit fulfill jobs for archived papers."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from paper_reviewer.models.paper import get_paper_by_id
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    FulfillPapersMetadataEnqueueResult,
    PaperAspectStatus,
)


def needs_fulfill_paper_metadata(
    source_record_status: PaperAspectStatus,
    full_text_status: PaperAspectStatus,
) -> bool:
    """Return True when fulfill still needs to run for these statuses."""
    if source_record_status is PaperAspectStatus.not_started:
        return True
    return (
        source_record_status is PaperAspectStatus.succeeded
        and full_text_status is PaperAspectStatus.not_started
    )


def enqueue_fulfill_papers_metadata(
    session: Session,
    paper_ids: list[int],
    *,
    submit_fulfill: Callable[[int, str], None],
) -> FulfillPapersMetadataEnqueueResult:
    """Select papers that need fulfill work and submit one job per selected id.

    Submits when source record is ``not_started``, or when source record is
    ``succeeded`` and full text is ``not_started``. Calls
    ``submit_fulfill(paper_id, doi)`` only for papers that should be enqueued.
    """
    submitted: list[int] = []
    skipped_terminal: list[int] = []

    for paper_id in paper_ids:
        paper = get_paper_by_id(session, paper_id)
        if paper is None:
            continue
        if needs_fulfill_paper_metadata(
            paper.source_record_status,
            paper.full_text_status,
        ):
            submit_fulfill(paper_id, paper.doi)
            submitted.append(paper_id)
            continue
        skipped_terminal.append(paper_id)

    return FulfillPapersMetadataEnqueueResult(
        submitted_paper_ids=submitted,
        skipped_already_terminal=skipped_terminal,
    )
