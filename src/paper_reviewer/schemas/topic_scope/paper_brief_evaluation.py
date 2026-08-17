"""Paper brief evaluation: G-Eval JSON and evaluate-brief result contracts."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from pydantic import BaseModel, Field

from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)


class GEvalCriterionScore(BaseModel):
    """One G-Eval criterion: step-by-step reasoning plus integer score 1–5."""

    reasoning: str
    score: int = Field(ge=1, le=5)


class PaperBriefEvaluation(BaseModel):
    """LLM JSON and persisted ``evaluation`` JSONB. No overall mean field."""

    faithfulness: GEvalCriterionScore
    completeness: GEvalCriterionScore
    conciseness: GEvalCriterionScore
    topic_agnostic: GEvalCriterionScore


class EvaluatePaperBriefResult(BaseModel):
    """Result of scoring or skipping evaluation for one PaperBrief."""

    paper_id: int
    status: PaperAspectStatus
    error_message: str | None = None


def mean_evaluation_score(evaluation: PaperBriefEvaluation) -> Decimal:
    """Return the mean of the four criterion scores, two decimal places."""
    total = (
        evaluation.faithfulness.score
        + evaluation.completeness.score
        + evaluation.conciseness.score
        + evaluation.topic_agnostic.score
    )
    return (Decimal(total) / Decimal(4)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
