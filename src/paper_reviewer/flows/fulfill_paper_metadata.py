"""Prefect flow: default-skip orchestrator for one Paper."""

from __future__ import annotations

from prefect import flow

from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    FulfillPaperMetadataResult,
)
from paper_reviewer.topic_scope.fulfill_papers_metadata.inform import (
    fulfill_paper_metadata as _fulfill_paper_metadata,
)


@flow(name="fulfill_paper_metadata", flow_run_name="{doi}")
def fulfill_paper_metadata(paper_id: int, doi: str) -> FulfillPaperMetadataResult:
    """Idempotent Prefect entrypoint: fulfill both aspects for one Paper.

    ``doi`` is a Prefect parameter for UI/search and the flow run name
    (including subflows); durable work keys off ``paper_id``.
    """
    return _fulfill_paper_metadata(paper_id)
