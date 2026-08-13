"""Prefect flow: fill the full-text aspect for one Paper."""

from __future__ import annotations

from prefect import flow

from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    InformFullTextResult,
)
from paper_reviewer.topic_brief_generation.fulfill_papers_metadata.inform import (
    inform_full_text as _inform_full_text,
)


@flow(name="inform_full_text")
def inform_full_text(paper_id: int, doi: str) -> InformFullTextResult:
    """Idempotent Prefect entrypoint: full-text one Paper by id.

    ``doi`` is a Prefect parameter for UI/search (and submit-time run names);
    durable work keys off ``paper_id``.
    """
    return _inform_full_text(paper_id)
