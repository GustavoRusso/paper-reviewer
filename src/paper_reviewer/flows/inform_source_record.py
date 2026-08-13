"""Prefect flow: fill the source-record aspect for one Paper."""

from __future__ import annotations

from prefect import flow

from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    InformSourceRecordResult,
)
from paper_reviewer.topic_brief_generation.fulfill_papers_metadata.inform import (
    inform_source_record as _inform_source_record,
)


@flow(name="inform_source_record")
def inform_source_record(paper_id: int, doi: str) -> InformSourceRecordResult:
    """Idempotent Prefect entrypoint: source-record one Paper by id.

    ``doi`` is a Prefect parameter for UI/search (and submit-time run names);
    durable work keys off ``paper_id``.
    """
    return _inform_source_record(paper_id)
