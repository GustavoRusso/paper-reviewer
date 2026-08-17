"""Prefect flow: evaluate a global PaperBrief for one Paper."""

from __future__ import annotations

from prefect import flow

from paper_reviewer.schemas.topic_scope.paper_brief_evaluation import (
    EvaluatePaperBriefResult,
)
from paper_reviewer.topic_scope.paper_brief_evaluation.evaluate import (
    evaluate_paper_brief as _evaluate_paper_brief,
)


@flow(name="evaluate_paper_brief", flow_run_name="{doi}")
def evaluate_paper_brief(
    paper_id: int,
    doi: str,
    force: bool = False,
) -> EvaluatePaperBriefResult:
    """Idempotent Prefect entrypoint: score one succeeded PaperBrief.

    ``doi`` is a Prefect parameter for UI/search and the flow run name
    (including subflows); durable work keys off ``paper_id``. Standalone runs
    do not pass ``force``.
    """
    return _evaluate_paper_brief(paper_id, force=force)
