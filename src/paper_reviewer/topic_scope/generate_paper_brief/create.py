"""Create or skip a global PaperBrief for one Paper."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory
from paper_reviewer.ingest.pubmed.pmc_cloud import usable_full_text_plain
from paper_reviewer.models.paper import get_paper_by_id
from paper_reviewer.models.paper_brief import (
    PaperBrief,
    create_paper_brief_row,
    get_paper_brief_by_paper_id,
)
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    CreatePaperBriefResult,
    PaperBriefContent,
    PaperBriefLlmResult,
)

GeneratePaperBriefContent = Callable[..., PaperBriefContent | PaperBriefLlmResult]

_TERMINAL_BRIEF_STATUSES = {
    PaperAspectStatus.succeeded,
    PaperAspectStatus.failed,
    PaperAspectStatus.unavailable,
}


def _default_session_factory() -> sessionmaker[Session]:
    return create_session_factory(create_db_engine())


def _default_generate_content(
    full_text_plain: str,
    *,
    title: str,
    journal: str | None,
    published_year: int | None,
) -> PaperBriefLlmResult:
    from paper_reviewer.topic_scope.generate_paper_brief.llm import (
        generate_paper_brief_content,
    )

    return generate_paper_brief_content(
        full_text_plain,
        title=title,
        journal=journal,
        published_year=published_year,
    )


def _result(paper_id: int, brief: PaperBrief | None) -> CreatePaperBriefResult:
    if brief is None:
        return CreatePaperBriefResult(
            paper_id=paper_id,
            status=PaperAspectStatus.not_started,
        )
    return CreatePaperBriefResult(
        paper_id=paper_id,
        status=brief.status,
        error_message=brief.error_message,
    )


def _clear_evaluation(brief: PaperBrief) -> None:
    brief.evaluation_status = PaperAspectStatus.not_started
    brief.evaluation = None
    brief.evaluation_score = None
    brief.evaluation_error_message = None


def _mark_failed(
    session: Session,
    paper_id: int,
    brief: PaperBrief | None,
    message: str,
) -> CreatePaperBriefResult:
    if brief is None:
        brief = create_paper_brief_row(session, paper_id=paper_id)
    brief.status = PaperAspectStatus.failed
    brief.error_message = message
    brief.content = None
    brief.prompt_tokens = None
    brief.completion_tokens = None
    brief.total_tokens = None
    _clear_evaluation(brief)
    session.commit()
    return _result(paper_id, brief)


def create_paper_brief(
    paper_id: int,
    *,
    force: bool = False,
    session_factory: sessionmaker[Session] | None = None,
    generate_content: GeneratePaperBriefContent | None = None,
) -> CreatePaperBriefResult:
    """Draft a PaperBrief when full text succeeded, with default skip rules."""
    factory = session_factory or _default_session_factory()
    generate = generate_content or _default_generate_content
    session = factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        if paper is None:
            return CreatePaperBriefResult(
                paper_id=paper_id,
                status=PaperAspectStatus.failed,
                error_message=f"Paper id {paper_id} not found",
            )
        brief = get_paper_brief_by_paper_id(session, paper_id)
        if paper.full_text_status is not PaperAspectStatus.succeeded:
            return _result(paper_id, brief)
        if (
            not force
            and brief is not None
            and brief.status in _TERMINAL_BRIEF_STATUSES
        ):
            return _result(paper_id, brief)
        if usable_full_text_plain(paper.full_text_plain) is None:
            return _mark_failed(
                session,
                paper_id,
                brief,
                "full_text_plain is not usable article body",
            )
        try:
            generated = generate(
                paper.full_text_plain,
                title=paper.title,
                journal=paper.journal,
                published_year=paper.published_year,
            )
        except Exception as exc:
            return _mark_failed(session, paper_id, brief, str(exc))
        if isinstance(generated, PaperBriefLlmResult):
            content = generated.content
            prompt_tokens = generated.prompt_tokens
            completion_tokens = generated.completion_tokens
            total_tokens = generated.total_tokens
        else:
            content = generated
            prompt_tokens = None
            completion_tokens = None
            total_tokens = None
        if brief is None:
            brief = create_paper_brief_row(session, paper_id=paper_id)
        brief.content = content.model_dump(mode="json")
        brief.prompt_tokens = prompt_tokens
        brief.completion_tokens = completion_tokens
        brief.total_tokens = total_tokens
        brief.status = PaperAspectStatus.succeeded
        brief.error_message = None
        _clear_evaluation(brief)
        session.commit()
        return _result(paper_id, brief)
    finally:
        session.close()
