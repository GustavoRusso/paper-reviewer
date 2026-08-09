"""Start Topic brief generation from Topic intake text."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.topic_brief_generation import TopicBriefGeneration
from paper_reviewer.schemas.topic_intake import TopicStatement


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    # Register mapped tables before create_all.
    import paper_reviewer.models.topic_brief_generation  # noqa: F401

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


def test_start_topic_brief_from_topic_intake_persists_and_returns_public_id(
    session: Session,
) -> None:
    from paper_reviewer.models.topic_brief_generation import (
        get_topic_brief_generation_by_public_id,
        start_topic_brief_from_topic_intake,
    )

    topic_statement, generation = start_topic_brief_from_topic_intake(
        session,
        "  GLP-1 agonists in heart failure  ",
    )

    assert isinstance(topic_statement, TopicStatement)
    assert topic_statement.text == "GLP-1 agonists in heart failure"
    assert isinstance(generation, TopicBriefGeneration)
    assert isinstance(generation.public_id, uuid.UUID)
    assert generation.topic_statement == topic_statement.text

    found = get_topic_brief_generation_by_public_id(session, generation.public_id)
    assert found is not None
    assert found.id == generation.id


def test_start_topic_brief_from_topic_intake_rejects_empty(session: Session) -> None:
    from paper_reviewer.models.topic_brief_generation import (
        start_topic_brief_from_topic_intake,
    )

    with pytest.raises(ValidationError):
        start_topic_brief_from_topic_intake(session, "   ")
