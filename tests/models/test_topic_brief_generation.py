"""Topic brief generation: create and look up by public id."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.topic_brief_generation import (
    TopicBriefGeneration,
    create_topic_brief_generation,
    get_topic_brief_generation_by_public_id,
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


def test_create_topic_brief_generation_stores_query_and_ids(session: Session) -> None:
    generation = create_topic_brief_generation(
        session,
        "GLP-1 agonists in heart failure",
    )
    session.flush()

    assert generation.research_query == "GLP-1 agonists in heart failure"
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
    assert found.research_query == "mitochondrial dysfunction"


def test_get_topic_brief_generation_by_public_id_returns_none_when_missing(
    session: Session,
) -> None:
    found = get_topic_brief_generation_by_public_id(session, uuid.uuid4())

    assert found is None
