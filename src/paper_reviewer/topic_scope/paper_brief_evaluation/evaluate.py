"""Evaluate or skip a global PaperBrief for one Paper."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory
from paper_reviewer.ingest.pubmed.pmc_cloud import usable_full_text_plain
from paper_reviewer.models.paper import get_paper_by_id
from paper_reviewer.models.paper_brief import PaperBrief, get_paper_brief_by_paper_id
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    PaperBriefContent,
)
from paper_reviewer.schemas.topic_scope.paper_brief_evaluation import (
    EvaluatePaperBriefResult,
    PaperBriefEvaluation,
    mean_evaluation_score,
)
from paper_reviewer.topic_scope.generate_paper_brief.llm import (
    format_exception_message,
)

JudgePaperBriefEvaluation = Callable[..., PaperBriefEvaluation]

_TERMINAL_EVALUATION_STATUSES = {
    PaperAspectStatus.succeeded,
    PaperAspectStatus.failed,
}


def _default_session_factory() -> sessionmaker[Session]:
    return create_session_factory(create_db_engine())


def _default_judge(
    full_text_plain: str,
    *,
    content: PaperBriefContent,
) -> PaperBriefEvaluation:
    from paper_reviewer.topic_scope.paper_brief_evaluation.llm import (
        judge_paper_brief_evaluation,
    )

    return judge_paper_brief_evaluation(full_text_plain, content=content)


def _result(paper_id: int, brief: PaperBrief | None) -> EvaluatePaperBriefResult:
    if brief is None:
        return EvaluatePaperBriefResult(
            paper_id=paper_id,
            status=PaperAspectStatus.not_started,
        )
    return EvaluatePaperBriefResult(
        paper_id=paper_id,
        status=brief.evaluation_status,
        error_message=brief.evaluation_error_message,
    )


def _mark_evaluation_failed(
    session: Session,
    paper_id: int,
    brief: PaperBrief,
    message: str,
) -> EvaluatePaperBriefResult:
    brief.evaluation_status = PaperAspectStatus.failed
    brief.evaluation_error_message = message
    brief.evaluation = None
    brief.evaluation_score = None
    session.commit()
    return _result(paper_id, brief)


def evaluate_paper_brief(
    paper_id: int,
    *,
    force: bool = False,
    session_factory: sessionmaker[Session] | None = None,
    judge_evaluation: JudgePaperBriefEvaluation | None = None,
) -> EvaluatePaperBriefResult:
    """Score a succeeded PaperBrief when full text is usable.

    Does not create a PaperBrief row. Does not change brief ``status``,
    ``content``, or generate-brief token columns.
    """
    factory = session_factory or _default_session_factory()
    judge = judge_evaluation or _default_judge
    session = factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        if paper is None:
            return EvaluatePaperBriefResult(
                paper_id=paper_id,
                status=PaperAspectStatus.failed,
                error_message=f"Paper id {paper_id} not found",
            )
        brief = get_paper_brief_by_paper_id(session, paper_id)
        if brief is None or brief.status is not PaperAspectStatus.succeeded:
            return _result(paper_id, brief)
        if not force and brief.evaluation_status in _TERMINAL_EVALUATION_STATUSES:
            return _result(paper_id, brief)
        if usable_full_text_plain(paper.full_text_plain) is None:
            return _mark_evaluation_failed(
                session,
                paper_id,
                brief,
                "full_text_plain is not usable article body",
            )
        try:
            content = PaperBriefContent.model_validate(brief.content)
            evaluation = judge(paper.full_text_plain, content=content)
        except Exception as exc:
            return _mark_evaluation_failed(
                session, paper_id, brief, format_exception_message(exc)
            )
        brief.evaluation = evaluation.model_dump(mode="json")
        brief.evaluation_score = mean_evaluation_score(evaluation)
        brief.evaluation_status = PaperAspectStatus.succeeded
        brief.evaluation_error_message = None
        session.commit()
        return _result(paper_id, brief)
    finally:
        session.close()
