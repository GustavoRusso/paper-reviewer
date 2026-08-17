"""Prefect flow: force-regenerate one Paper (source, full text, brief)."""

from __future__ import annotations

from prefect import flow

from paper_reviewer.flows.create_paper_brief import create_paper_brief
from paper_reviewer.flows.inform_full_text import inform_full_text
from paper_reviewer.flows.inform_source_record import inform_source_record
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
    RegeneratePaperResult,
)


@flow(name="regenerate_paper")
def regenerate_paper(paper_id: int, doi: str) -> RegeneratePaperResult:
    """Force Prefect entrypoint: regenerate one Paper by id.

    ``doi`` is a Prefect parameter for UI/search (and submit-time run names);
    durable work keys off ``paper_id``. Always forces; do not pass ``force``.
    Calls leaf flows as subflows.
    """
    source = inform_source_record(paper_id, doi, force=True)
    full_text = inform_full_text(paper_id, doi, force=True)
    brief = None
    if full_text.status is PaperAspectStatus.succeeded:
        brief = create_paper_brief(paper_id, doi, force=True)
    return RegeneratePaperResult(
        paper_id=paper_id,
        source_record=source,
        full_text=full_text,
        brief=brief,
    )
