"""Topic scope: create, look up, and list."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.topic_brief_generation import (
    TopicScope,
    create_topic_scope,
    get_topic_scope_by_key,
    list_topic_scopes,
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
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


def test_create_topic_scope_stores_statement_and_ids(
    session: Session,
) -> None:
    topic_scope = create_topic_scope(
        session,
        "GLP-1 agonists in heart failure",
    )
    session.flush()

    assert topic_scope.topic_statement == "GLP-1 agonists in heart failure"
    assert isinstance(topic_scope.id, int)
    assert topic_scope.id > 0
    assert isinstance(topic_scope.key, uuid.UUID)
    assert isinstance(topic_scope, TopicScope)


def test_get_topic_scope_by_key(session: Session) -> None:
    created = create_topic_scope(session, "mitochondrial dysfunction")
    session.flush()

    found = get_topic_scope_by_key(session, created.key)

    assert found is not None
    assert found.id == created.id
    assert found.key == created.key
    assert found.topic_statement == "mitochondrial dysfunction"


def test_get_topic_scope_by_key_returns_none_when_missing(
    session: Session,
) -> None:
    found = get_topic_scope_by_key(session, uuid.uuid4())

    assert found is None


def test_list_topic_scopes_empty(session: Session) -> None:
    assert list(list_topic_scopes(session)) == []


def test_list_topic_scopes_newest_first(session: Session) -> None:
    older = create_topic_scope(session, "older topic")
    newer = create_topic_scope(session, "newer topic")
    session.flush()
    # Pin timestamps so order is deterministic across backends.
    older.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    newer.created_at = datetime(2026, 8, 12, tzinfo=UTC)
    session.flush()

    listed = list(list_topic_scopes(session))

    assert [row.topic_statement for row in listed] == ["newer topic", "older topic"]
    assert listed[0].key == newer.key
    assert listed[1].key == older.key
    assert all(isinstance(row, TopicScope) for row in listed)
