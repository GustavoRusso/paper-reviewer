"""Prefect flow: create a global PaperBrief for one Paper."""

from __future__ import annotations

from prefect import flow

from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    CreatePaperBriefResult,
)
from paper_reviewer.topic_scope.generate_paper_brief.create import (
    create_paper_brief as _create_paper_brief,
)


@flow(name="create_paper_brief", flow_run_name="{doi}")
def create_paper_brief(
    paper_id: int,
    doi: str,
    force: bool = False,
) -> CreatePaperBriefResult:
    """Idempotent Prefect entrypoint: draft one PaperBrief.

    ``doi`` is a Prefect parameter for UI/search and the flow run name
    (including subflows); durable work keys off ``paper_id``. Standalone runs
    do not pass ``force``.
    """
    return _create_paper_brief(paper_id, force=force)
