"""create_topic_brief: briefed gate, overwrite, and stub LLM writes."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.topic_scope.topic_brief import (
    create_topic_brief_row,
    get_topic_brief_by_topic_scope_id,
)
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.topic_brief_generation import (
    TopicBriefContent,
)
from paper_reviewer.topic_scope.topic_brief_generation import create_topic_brief
from paper_reviewer.topic_scope.topic_brief_generation.create import (
    ZERO_BRIEFED_ERROR,
)
from tests.topic_scope.topic_brief_generation.helpers import (
    add_briefed_reference,
    create_test_scope,
    sample_topic_brief_content,
)


def test_creates_succeeded_when_briefed_and_no_row(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    add_briefed_reference(session_factory, topic_scope_id)
    calls: list[str] = []

    def generate(*, topic_statement: str) -> TopicBriefContent:
        calls.append(topic_statement)
        return sample_topic_brief_content(title="Drafted title for this topic")

    result = create_topic_brief(
        topic_scope_id,
        session_factory=session_factory,
        generate_content=generate,
    )

    assert result.status is PaperAspectStatus.succeeded
    assert result.error_message is None
    assert calls == ["glioblastoma immunotherapy"]

    session = session_factory()
    try:
        brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
        assert brief is not None
        assert brief.content is not None
        assert brief.content["title"] == "Drafted title for this topic"
    finally:
        session.close()


def test_force_rewrites_succeeded_content(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    add_briefed_reference(session_factory, topic_scope_id)
    session = session_factory()
    try:
        row = create_topic_brief_row(session, topic_scope_id=topic_scope_id)
        row.status = PaperAspectStatus.succeeded
        row.content = sample_topic_brief_content(title="Old title").model_dump(
            mode="json"
        )
        session.commit()
    finally:
        session.close()

    result = create_topic_brief(
        topic_scope_id,
        force=True,
        session_factory=session_factory,
        generate_content=lambda **_k: sample_topic_brief_content(
            title="New title after rewrite"
        ),
    )

    assert result.status is PaperAspectStatus.succeeded
    session = session_factory()
    try:
        brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
        assert brief is not None
        assert brief.content is not None
        assert brief.content["title"] == "New title after rewrite"
    finally:
        session.close()


def test_force_false_skips_when_succeeded(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    add_briefed_reference(session_factory, topic_scope_id)
    session = session_factory()
    try:
        row = create_topic_brief_row(session, topic_scope_id=topic_scope_id)
        row.status = PaperAspectStatus.succeeded
        row.content = sample_topic_brief_content(title="Keep me").model_dump(
            mode="json"
        )
        session.commit()
    finally:
        session.close()
    calls: list[str] = []

    result = create_topic_brief(
        topic_scope_id,
        force=False,
        session_factory=session_factory,
        generate_content=lambda **_k: calls.append("llm")
        or sample_topic_brief_content(),
    )

    assert result.status is PaperAspectStatus.succeeded
    assert calls == []


def test_zero_briefed_fails_without_llm_and_keeps_prior_content(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    session = session_factory()
    try:
        row = create_topic_brief_row(session, topic_scope_id=topic_scope_id)
        row.status = PaperAspectStatus.succeeded
        row.content = sample_topic_brief_content(title="Prior good").model_dump(
            mode="json"
        )
        session.commit()
    finally:
        session.close()
    calls: list[str] = []

    result = create_topic_brief(
        topic_scope_id,
        session_factory=session_factory,
        generate_content=lambda **_k: calls.append("llm")
        or sample_topic_brief_content(),
    )

    assert result.status is PaperAspectStatus.failed
    assert result.error_message == ZERO_BRIEFED_ERROR
    assert calls == []

    session = session_factory()
    try:
        brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
        assert brief is not None
        assert brief.content is not None
        assert brief.content["title"] == "Prior good"
    finally:
        session.close()


def test_llm_failure_keeps_prior_content(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    add_briefed_reference(session_factory, topic_scope_id)
    session = session_factory()
    try:
        row = create_topic_brief_row(session, topic_scope_id=topic_scope_id)
        row.status = PaperAspectStatus.succeeded
        row.content = sample_topic_brief_content(title="Prior good").model_dump(
            mode="json"
        )
        session.commit()
    finally:
        session.close()

    def boom(**_kwargs: object) -> TopicBriefContent:
        raise RuntimeError("llm down")

    result = create_topic_brief(
        topic_scope_id,
        session_factory=session_factory,
        generate_content=boom,
    )

    assert result.status is PaperAspectStatus.failed
    assert result.error_message == "llm down"

    session = session_factory()
    try:
        brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
        assert brief is not None
        assert brief.content is not None
        assert brief.content["title"] == "Prior good"
    finally:
        session.close()
