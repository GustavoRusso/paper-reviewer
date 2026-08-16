"""Reference ORM: create, list for a Topic scope, uniqueness."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.paper import create_paper
from paper_reviewer.models.topic_brief_generation import create_topic_scope
from paper_reviewer.models.topic_brief_generation.reference import (
    Reference,
    create_reference,
    list_references_for_scope,
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


def _add_paper(
    session: Session,
    *,
    doi: str,
    source_uid: str,
    title: str,
) -> int:
    paper = create_paper(
        session,
        doi=doi,
        source_id="pubmed",
        source_uid=source_uid,
        title=title,
        authors=["Ada Lovelace"],
        url=f"https://example.com/{source_uid}",
        journal="Nature",
        published_year=2024,
    )
    session.flush()
    return paper.id


def test_create_reference_stores_scope_paper_and_created_at(
    session: Session,
) -> None:
    topic_scope = create_topic_scope(session, "glioblastoma immunotherapy")
    session.flush()
    paper_id = _add_paper(
        session,
        doi="10.1000/A",
        source_uid="1",
        title="Paper A",
    )

    row = create_reference(session, topic_scope.id, paper_id)
    session.flush()
    session.refresh(row)

    assert isinstance(row, Reference)
    assert row.id > 0
    assert row.topic_scope_id == topic_scope.id
    assert row.paper_id == paper_id
    assert row.created_at is not None


def test_list_references_for_scope_orders_by_created_at_then_id(
    session: Session,
) -> None:
    topic_scope = create_topic_scope(session, "order test")
    session.flush()
    first_id = _add_paper(
        session, doi="10.1000/FIRST", source_uid="10", title="First"
    )
    second_id = _add_paper(
        session, doi="10.1000/SECOND", source_uid="11", title="Second"
    )
    later = datetime(2026, 1, 2, tzinfo=UTC)
    earlier = datetime(2026, 1, 1, tzinfo=UTC)
    create_reference(
        session, topic_scope.id, second_id
    ).created_at = later
    create_reference(
        session, topic_scope.id, first_id
    ).created_at = earlier
    session.flush()

    listed = list_references_for_scope(session, topic_scope.id)

    assert [paper.title for _ref, paper in listed] == ["First", "Second"]


def test_list_references_for_scope_excludes_other_scopes(
    session: Session,
) -> None:
    scope_a = create_topic_scope(session, "scope a")
    scope_b = create_topic_scope(session, "scope b")
    session.flush()
    paper_id = _add_paper(
        session, doi="10.1000/SHARED", source_uid="20", title="Shared"
    )
    create_reference(session, scope_a.id, paper_id)
    session.flush()

    listed_b = list_references_for_scope(session, scope_b.id)

    assert listed_b == []


def test_unique_topic_scope_id_and_paper_id(session: Session) -> None:
    topic_scope = create_topic_scope(session, "duplicate link")
    session.flush()
    paper_id = _add_paper(
        session, doi="10.1000/DUP", source_uid="30", title="Dup"
    )
    create_reference(session, topic_scope.id, paper_id)
    session.flush()

    create_reference(session, topic_scope.id, paper_id)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()
