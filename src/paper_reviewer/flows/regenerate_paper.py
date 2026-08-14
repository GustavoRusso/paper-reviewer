"""Prefect flow: force-regenerate one Paper (source, full text, brief)."""

from __future__ import annotations

from prefect import flow

from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    RegeneratePaperResult,
)
from paper_reviewer.topic_brief_generation.fulfill_papers_metadata.inform import (
    regenerate_paper as _regenerate_paper,
)


@flow(name="regenerate_paper")
def regenerate_paper(paper_id: int, doi: str) -> RegeneratePaperResult:
    """Force Prefect entrypoint: regenerate one Paper by id.

    ``doi`` is a Prefect parameter for UI/search (and submit-time run names);
    durable work keys off ``paper_id``. Always forces; do not pass ``force``.
    """
    return _regenerate_paper(paper_id)
