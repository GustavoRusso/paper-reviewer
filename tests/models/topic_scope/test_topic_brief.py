"""TopicBrief ORM: unique topic_scope_id, default status, content round-trip."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.topic_scope import create_topic_scope
from paper_reviewer.models.topic_scope.topic_brief import (
    TopicBrief,
    create_topic_brief_row,
    get_topic_brief_by_topic_scope_id,
)
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.topic_brief_generation import (
    TopicBriefContent,
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    import paper_reviewer.models.topic_scope.topic_brief  # noqa: F401
    import paper_reviewer.models.topic_scope.topic_scope  # noqa: F401

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        engine.dispose()


def test_create_topic_brief_defaults_not_started(session: Session) -> None:
    topic_scope = create_topic_scope(session, "statement")
    session.flush()
    brief = create_topic_brief_row(session, topic_scope_id=topic_scope.id)
    session.flush()

    assert isinstance(brief, TopicBrief)
    assert brief.topic_scope_id == topic_scope.id
    assert brief.status is PaperAspectStatus.not_started
    assert brief.error_message is None
    assert brief.content is None
    assert brief.prompt_tokens is None
    assert brief.completion_tokens is None
    assert brief.total_tokens is None
    assert brief.created_at is not None


def test_get_topic_brief_by_topic_scope_id(session: Session) -> None:
    topic_scope = create_topic_scope(session, "statement")
    session.flush()
    created = create_topic_brief_row(session, topic_scope_id=topic_scope.id)
    session.flush()

    found = get_topic_brief_by_topic_scope_id(session, topic_scope.id)

    assert found is not None
    assert found.id == created.id


def test_topic_scope_id_must_be_unique(session: Session) -> None:
    topic_scope = create_topic_scope(session, "statement")
    session.flush()
    create_topic_brief_row(session, topic_scope_id=topic_scope.id)
    session.flush()
    create_topic_brief_row(session, topic_scope_id=topic_scope.id)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_content_round_trip(session: Session) -> None:
    topic_scope = create_topic_scope(session, "statement")
    session.flush()
    brief = create_topic_brief_row(session, topic_scope_id=topic_scope.id)
    payload = TopicBriefContent(
        title="Example topic brief title for indexing",
        abstract="Abstract text.",
        introduction="Intro.[1]",
        sections=[{"heading": "Theme", "body": "Body.[1]"}],
        concluding_section="Close.",
        key_points=["Point"],
        citations=[{"n": 1, "doi": "10.1000/A", "text": "10.1000/A — Title"}],
    )
    brief.content = payload.model_dump(mode="json")
    brief.status = PaperAspectStatus.succeeded
    session.flush()

    found = get_topic_brief_by_topic_scope_id(session, topic_scope.id)
    assert found is not None
    assert found.content is not None
    loaded = TopicBriefContent.model_validate(found.content)
    assert loaded.title.startswith("Example")
    assert loaded.citations[0].doi == "10.1000/A"


def test_usage_integers_round_trip(session: Session) -> None:
    topic_scope = create_topic_scope(session, "statement")
    session.flush()
    brief = create_topic_brief_row(session, topic_scope_id=topic_scope.id)
    brief.prompt_tokens = 21
    brief.completion_tokens = 8
    brief.total_tokens = 29
    session.flush()

    found = get_topic_brief_by_topic_scope_id(session, topic_scope.id)
    assert found is not None
    assert found.prompt_tokens == 21
    assert found.completion_tokens == 8
    assert found.total_tokens == 29
