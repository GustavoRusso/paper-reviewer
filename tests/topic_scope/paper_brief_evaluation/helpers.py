"""Shared helpers for paper brief evaluation domain tests."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.paper_brief import get_paper_brief_by_paper_id
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    PaperBriefContent,
)
from paper_reviewer.schemas.topic_scope.paper_brief_evaluation import (
    GEvalCriterionScore,
    PaperBriefEvaluation,
)
from tests.topic_scope.generate_paper_brief.helpers import add_brief


def sample_criterion(
    *,
    reasoning: str = "Meets the contract.",
    score: int = 4,
) -> GEvalCriterionScore:
    return GEvalCriterionScore(reasoning=reasoning, score=score)


def sample_evaluation(**overrides: object) -> PaperBriefEvaluation:
    data: dict[str, object] = {
        "faithfulness": sample_criterion(
            reasoning="Claims match the full text.",
            score=5,
        ),
        "completeness": sample_criterion(
            reasoning="Required fields are filled.",
            score=4,
        ),
        "conciseness": sample_criterion(
            reasoning="Shape matches the template.",
            score=4,
        ),
        "topic_agnostic": sample_criterion(
            reasoning="The brief describes the article.",
            score=4,
        ),
    }
    data.update(overrides)
    return PaperBriefEvaluation.model_validate(data)


def add_succeeded_brief(
    factory: sessionmaker[Session],
    paper_id: int,
    *,
    content: PaperBriefContent | None = None,
    prompt_tokens: int | None = 11,
    completion_tokens: int | None = 7,
    total_tokens: int | None = 18,
) -> None:
    add_brief(
        factory,
        paper_id,
        status=PaperAspectStatus.succeeded,
        content=content,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )


def set_evaluation(
    factory: sessionmaker[Session],
    paper_id: int,
    *,
    status: PaperAspectStatus,
    evaluation: PaperBriefEvaluation | None = None,
    evaluation_score: Decimal | None = None,
    evaluation_error_message: str | None = None,
) -> None:
    session = factory()
    try:
        brief = get_paper_brief_by_paper_id(session, paper_id)
        assert brief is not None
        brief.evaluation_status = status
        brief.evaluation = (
            evaluation.model_dump(mode="json") if evaluation is not None else None
        )
        brief.evaluation_score = evaluation_score
        brief.evaluation_error_message = evaluation_error_message
        session.commit()
    finally:
        session.close()
