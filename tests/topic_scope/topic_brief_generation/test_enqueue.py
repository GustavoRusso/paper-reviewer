"""enqueue_create_topic_brief: zero-briefed, in-flight, and submit path."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.topic_scope.topic_brief import (
    create_topic_brief_row,
    get_topic_brief_by_topic_scope_id,
)
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.topic_scope.topic_brief_generation import (
    enqueue_create_topic_brief,
)
from tests.topic_scope.topic_brief_generation.helpers import (
    add_briefed_reference,
    create_test_scope,
    sample_topic_brief_content,
)


def test_enqueue_skips_when_zero_briefed(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    submitted: list[int] = []

    session = session_factory()
    try:
        result = enqueue_create_topic_brief(
            session,
            topic_scope_id,
            submit=submitted.append,
        )
    finally:
        session.close()

    assert result.submitted is False
    assert result.skipped_no_briefed is True
    assert result.skipped_in_flight is False
    assert submitted == []


def test_enqueue_skips_when_already_not_started(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    add_briefed_reference(session_factory, topic_scope_id)
    session = session_factory()
    try:
        create_topic_brief_row(
            session,
            topic_scope_id=topic_scope_id,
            status=PaperAspectStatus.not_started,
        )
        session.commit()
    finally:
        session.close()
    submitted: list[int] = []

    session = session_factory()
    try:
        result = enqueue_create_topic_brief(
            session,
            topic_scope_id,
            submit=submitted.append,
        )
    finally:
        session.close()

    assert result.submitted is False
    assert result.skipped_in_flight is True
    assert result.skipped_no_briefed is False
    assert submitted == []


def test_enqueue_submits_and_resets_row_keeping_content(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    add_briefed_reference(session_factory, topic_scope_id)
    session = session_factory()
    try:
        row = create_topic_brief_row(session, topic_scope_id=topic_scope_id)
        row.status = PaperAspectStatus.succeeded
        row.error_message = "old error"
        row.content = sample_topic_brief_content(title="Keep me").model_dump(
            mode="json"
        )
        session.commit()
    finally:
        session.close()
    submitted: list[int] = []

    session = session_factory()
    try:
        result = enqueue_create_topic_brief(
            session,
            topic_scope_id,
            submit=submitted.append,
        )
    finally:
        session.close()

    assert result.submitted is True
    assert result.skipped_in_flight is False
    assert result.skipped_no_briefed is False
    assert submitted == [topic_scope_id]

    session = session_factory()
    try:
        brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
        assert brief is not None
        assert brief.status is PaperAspectStatus.not_started
        assert brief.error_message is None
        assert brief.content is not None
        assert brief.content["title"] == "Keep me"
    finally:
        session.close()


def test_enqueue_creates_row_when_missing(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    add_briefed_reference(session_factory, topic_scope_id)
    submitted: list[int] = []

    session = session_factory()
    try:
        result = enqueue_create_topic_brief(
            session,
            topic_scope_id,
            submit=submitted.append,
        )
    finally:
        session.close()

    assert result.submitted is True
    assert submitted == [topic_scope_id]

    session = session_factory()
    try:
        brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
        assert brief is not None
        assert brief.status is PaperAspectStatus.not_started
    finally:
        session.close()
