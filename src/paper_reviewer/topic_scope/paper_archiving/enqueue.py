"""Select papers that need first ingest and submit ingest_paper."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from paper_reviewer.models.paper import get_paper_by_id
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.paper_archiving import (
    PaperArchivingResult,
    PaperIngestEnqueueResult,
)


def enqueue_ingest_papers(
    session: Session,
    archiving_result: PaperArchivingResult,
    *,
    submit_ingest: Callable[[int, str], None],
) -> PaperIngestEnqueueResult:
    """Submit ``ingest_paper`` for inserted and never-ingested papers.

    Submits when the paper id is in ``created_paper_ids``, or when a reused
    row still has ``source_record_status`` ``not_started``. Other papers in
    ``papers`` are skipped. Missing ids are dropped.
    """
    created = set(archiving_result.created_paper_ids)
    submitted: list[int] = []
    skipped_existed: list[int] = []

    for paper in archiving_result.papers:
        row = get_paper_by_id(session, paper.id)
        if row is None:
            continue
        if paper.id in created or row.source_record_status is PaperAspectStatus.not_started:
            submit_ingest(paper.id, row.doi)
            submitted.append(paper.id)
            continue
        skipped_existed.append(paper.id)

    return PaperIngestEnqueueResult(
        submitted_paper_ids=submitted,
        skipped_already_existed=skipped_existed,
    )
