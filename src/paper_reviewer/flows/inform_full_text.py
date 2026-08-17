"""Prefect flow: fill the full-text aspect for one Paper."""

from __future__ import annotations

from prefect import flow

from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    InformFullTextResult,
)
from paper_reviewer.topic_scope.fulfill_papers_metadata.inform import (
    inform_full_text as _inform_full_text,
)


@flow(name="inform_full_text", flow_run_name="{doi}")
def inform_full_text(
    paper_id: int,
    doi: str,
    force: bool = False,
) -> InformFullTextResult:
    """Idempotent Prefect entrypoint: full-text one Paper by id.

    ``doi`` is a Prefect parameter for UI/search and the flow run name
    (including subflows); durable work keys off ``paper_id``. ``force`` is for
    subflow calls from ``ingest_paper``; served deployments keep the
    default skip.
    """
    return _inform_full_text(paper_id, force=force)
