"""Apply selection rules and submit inform jobs for archived papers."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from paper_reviewer.models.topic_brief_generation.paper import get_paper_by_id
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    FulfillPapersMetadataEnqueueResult,
)


def enqueue_fulfill_papers_metadata(
    session: Session,
    paper_ids: list[int],
    *,
    submit_inform: Callable[[int, str], None],
) -> FulfillPapersMetadataEnqueueResult:
    """Select papers that need inform and submit one job per selected id.

    Skips papers that are already source-informed or already failed to fulfill
    metadata. Calls ``submit_inform(paper_id, doi)`` only for papers that
    should be enqueued.
    """
    submitted: list[int] = []
    skipped_informed: list[int] = []
    skipped_failed: list[int] = []

    for paper_id in paper_ids:
        paper = get_paper_by_id(session, paper_id)
        if paper is None:
            continue
        if paper.source_informed_at is not None:
            skipped_informed.append(paper_id)
            continue
        if paper.source_inform_error_message is not None:
            skipped_failed.append(paper_id)
            continue
        submit_inform(paper_id, paper.doi)
        submitted.append(paper_id)

    return FulfillPapersMetadataEnqueueResult(
        submitted_paper_ids=submitted,
        skipped_already_informed=skipped_informed,
        skipped_already_failed=skipped_failed,
    )
