"""Prefect flow: inform one Paper from its paper source."""

from __future__ import annotations

from prefect import flow

from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    InformPaperFromSourceResult,
)
from paper_reviewer.topic_brief_generation.fulfill_papers_metadata.inform import (
    inform_paper_from_source as _inform_paper_from_source,
)


@flow(name="inform_paper_from_source")
def inform_paper_from_source(paper_id: int, doi: str) -> InformPaperFromSourceResult:
    """Idempotent Prefect entrypoint: source-inform one Paper by id.

    ``doi`` is a Prefect parameter for UI/search (and submit-time run names);
    durable work keys off ``paper_id``.
    """
    return _inform_paper_from_source(paper_id)
