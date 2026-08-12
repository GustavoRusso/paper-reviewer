"""Topic brief generation: create, look up, and list."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.topic_brief_generation import (
    TopicBriefGeneration,
    create_topic_brief_generation,
    get_topic_brief_generation_by_public_id,
    list_topic_brief_generations,
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


def test_create_topic_brief_generation_stores_statement_and_ids(
    session: Session,
) -> None:
    generation = create_topic_brief_generation(
        session,
        "GLP-1 agonists in heart failure",
    )
    session.flush()

    assert generation.topic_statement == "GLP-1 agonists in heart failure"
    assert isinstance(generation.id, int)
    assert generation.id > 0
    assert isinstance(generation.public_id, uuid.UUID)
    assert isinstance(generation, TopicBriefGeneration)


def test_get_topic_brief_generation_by_public_id(session: Session) -> None:
    created = create_topic_brief_generation(session, "mitochondrial dysfunction")
    session.flush()

    found = get_topic_brief_generation_by_public_id(session, created.public_id)

    assert found is not None
    assert found.id == created.id
    assert found.public_id == created.public_id
    assert found.topic_statement == "mitochondrial dysfunction"


def test_get_topic_brief_generation_by_public_id_returns_none_when_missing(
    session: Session,
) -> None:
    found = get_topic_brief_generation_by_public_id(session, uuid.uuid4())

    assert found is None


def test_list_topic_brief_generations_empty(session: Session) -> None:
    assert list(list_topic_brief_generations(session)) == []


def test_list_topic_brief_generations_newest_first(session: Session) -> None:
    older = create_topic_brief_generation(session, "older topic")
    newer = create_topic_brief_generation(session, "newer topic")
    session.flush()
    # Pin timestamps so order is deterministic across backends.
    older.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    newer.created_at = datetime(2026, 8, 12, tzinfo=UTC)
    session.flush()

    listed = list(list_topic_brief_generations(session))

    assert [g.topic_statement for g in listed] == ["newer topic", "older topic"]
    assert listed[0].public_id == newer.public_id
    assert listed[1].public_id == older.public_id
    assert all(isinstance(g, TopicBriefGeneration) for g in listed)
