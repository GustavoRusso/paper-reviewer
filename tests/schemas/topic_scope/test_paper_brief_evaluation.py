"""Paper brief evaluation: G-Eval JSON, score bounds, and mean helper."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.paper_brief_evaluation import (
    EvaluatePaperBriefResult,
    GEvalCriterionScore,
    PaperBriefEvaluation,
    mean_evaluation_score,
)
from paper_reviewer.topic_scope.paper_brief_evaluation.llm import (
    evaluation_criterion_ids,
)


def _criterion(score: int) -> GEvalCriterionScore:
    return GEvalCriterionScore(reasoning="Step-by-step.", score=score)


def test_geval_criterion_score_accepts_one_through_five() -> None:
    for score in (1, 2, 3, 4, 5):
        item = GEvalCriterionScore(reasoning="ok", score=score)
        assert item.score == score


@pytest.mark.parametrize("score", [0, 6])
def test_geval_criterion_score_rejects_out_of_range(score: int) -> None:
    with pytest.raises(ValidationError):
        GEvalCriterionScore(reasoning="bad", score=score)


def test_paper_brief_evaluation_has_four_criteria() -> None:
    evaluation = PaperBriefEvaluation(
        faithfulness=_criterion(5),
        completeness=_criterion(4),
        conciseness=_criterion(4),
        topic_agnostic=_criterion(4),
    )

    assert list(PaperBriefEvaluation.model_fields) == [
        "faithfulness",
        "completeness",
        "conciseness",
        "topic_agnostic",
    ]
    dumped = evaluation.model_dump(mode="json")
    assert "evaluation_score" not in dumped
    assert "evaluation_score" not in PaperBriefEvaluation.model_fields


def test_paper_brief_evaluation_fields_match_template_front_matter() -> None:
    assert list(PaperBriefEvaluation.model_fields) == evaluation_criterion_ids()


def test_mean_evaluation_score_is_two_decimal_mean() -> None:
    evaluation = PaperBriefEvaluation(
        faithfulness=_criterion(5),
        completeness=_criterion(4),
        conciseness=_criterion(4),
        topic_agnostic=_criterion(4),
    )

    assert mean_evaluation_score(evaluation) == Decimal("4.25")


def test_mean_evaluation_score_range() -> None:
    low = PaperBriefEvaluation(
        faithfulness=_criterion(1),
        completeness=_criterion(1),
        conciseness=_criterion(1),
        topic_agnostic=_criterion(1),
    )
    high = PaperBriefEvaluation(
        faithfulness=_criterion(5),
        completeness=_criterion(5),
        conciseness=_criterion(5),
        topic_agnostic=_criterion(5),
    )

    assert mean_evaluation_score(low) == Decimal("1.00")
    assert mean_evaluation_score(high) == Decimal("5.00")


def test_evaluate_paper_brief_result() -> None:
    result = EvaluatePaperBriefResult(
        paper_id=10,
        status=PaperAspectStatus.succeeded,
    )

    assert result.paper_id == 10
    assert result.status is PaperAspectStatus.succeeded
    assert result.error_message is None
    assert "evaluation_score" not in EvaluatePaperBriefResult.model_fields
