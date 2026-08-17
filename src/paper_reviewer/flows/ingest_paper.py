"""Prefect flow: ingest one Paper (source, full text, brief, evaluation)."""

from __future__ import annotations

from prefect import flow

from paper_reviewer.flows.create_paper_brief import create_paper_brief
from paper_reviewer.flows.evaluate_paper_brief import evaluate_paper_brief
from paper_reviewer.flows.inform_full_text import inform_full_text
from paper_reviewer.flows.inform_source_record import inform_source_record
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    IngestPaperResult,
    PaperAspectStatus,
)


@flow(name="ingest_paper", flow_run_name="{doi}")
def ingest_paper(paper_id: int, doi: str) -> IngestPaperResult:
    """Force Prefect entrypoint: ingest one Paper by id.

    ``doi`` is a Prefect parameter for UI/search and the flow run name
    (including subflows); durable work keys off ``paper_id``. Always forces;
    do not pass ``force``. Calls leaf flows as subflows.
    """
    source = inform_source_record(paper_id, doi, force=True)
    full_text = inform_full_text(paper_id, doi, force=True)
    brief = None
    evaluation = None
    if full_text.status is PaperAspectStatus.succeeded:
        brief = create_paper_brief(paper_id, doi, force=True)
        if brief.status is PaperAspectStatus.succeeded:
            evaluation = evaluate_paper_brief(paper_id, doi, force=True)
    return IngestPaperResult(
        paper_id=paper_id,
        source_record=source,
        full_text=full_text,
        brief=brief,
        evaluation=evaluation,
    )
