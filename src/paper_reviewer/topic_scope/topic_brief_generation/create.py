"""Create or rewrite a TopicBrief for one Topic scope."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory
from paper_reviewer.models.topic_scope.topic_brief import (
    TopicBrief,
    create_topic_brief_row,
    get_topic_brief_by_topic_scope_id,
)
from paper_reviewer.models.topic_scope.topic_scope import TopicScope
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.topic_brief_generation import (
    CreateTopicBriefResult,
    TopicBriefContent,
)
from paper_reviewer.topic_scope.topic_brief_generation.briefed import (
    count_briefed_references,
)

GenerateTopicBriefContent = Callable[..., TopicBriefContent]

ZERO_BRIEFED_ERROR = (
    "Generation needs at least one Reference with a succeeded paper brief."
)


def _default_session_factory() -> sessionmaker[Session]:
    return create_session_factory(create_db_engine())


def _stub_topic_brief_content(**_kwargs: object) -> TopicBriefContent:
    """Step 2 walking-skeleton stub; Step 3 replaces with the real LLM client."""
    return TopicBriefContent(
        title="Example topic brief title for indexing",
        abstract="A short abstract without citations.",
        introduction="Background and why it matters.",
        sections=[{"heading": "Main theme", "body": "Discussion of evidence."}],
        concluding_section="Summary of the viewpoint.",
        key_points=["Key point one"],
        citations=[],
    )


def _result(
    topic_scope_id: int,
    brief: TopicBrief | None,
) -> CreateTopicBriefResult:
    if brief is None:
        return CreateTopicBriefResult(
            topic_scope_id=topic_scope_id,
            status=PaperAspectStatus.not_started,
        )
    return CreateTopicBriefResult(
        topic_scope_id=topic_scope_id,
        status=brief.status,
        error_message=brief.error_message,
    )


def _mark_failed(
    session: Session,
    topic_scope_id: int,
    brief: TopicBrief | None,
    message: str,
) -> CreateTopicBriefResult:
    if brief is None:
        brief = create_topic_brief_row(session, topic_scope_id=topic_scope_id)
    brief.status = PaperAspectStatus.failed
    brief.error_message = message
    session.commit()
    return _result(topic_scope_id, brief)


def _get_topic_scope(session: Session, topic_scope_id: int) -> TopicScope | None:
    return session.get(TopicScope, topic_scope_id)


def create_topic_brief(
    topic_scope_id: int,
    *,
    force: bool = True,
    session_factory: sessionmaker[Session] | None = None,
    generate_content: GenerateTopicBriefContent | None = None,
) -> CreateTopicBriefResult:
    """Draft a TopicBrief from briefed References (overwrite when force)."""
    factory = session_factory or _default_session_factory()
    generate = generate_content or _stub_topic_brief_content
    session = factory()
    try:
        topic_scope = _get_topic_scope(session, topic_scope_id)
        if topic_scope is None:
            return CreateTopicBriefResult(
                topic_scope_id=topic_scope_id,
                status=PaperAspectStatus.failed,
                error_message=f"Topic scope id {topic_scope_id} not found",
            )
        brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
        if count_briefed_references(session, topic_scope_id) == 0:
            return _mark_failed(
                session,
                topic_scope_id,
                brief,
                ZERO_BRIEFED_ERROR,
            )
        if (
            not force
            and brief is not None
            and brief.status is PaperAspectStatus.succeeded
        ):
            return _result(topic_scope_id, brief)
        try:
            content = generate(topic_statement=topic_scope.topic_statement)
        except Exception as exc:
            return _mark_failed(session, topic_scope_id, brief, str(exc))
        if brief is None:
            brief = create_topic_brief_row(session, topic_scope_id=topic_scope_id)
        brief.content = content.model_dump(mode="json")
        brief.status = PaperAspectStatus.succeeded
        brief.error_message = None
        session.commit()
        return _result(topic_scope_id, brief)
    finally:
        session.close()
