"""add_references: attach Papers to a Topic scope by DOI."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.paper import create_paper
from paper_reviewer.models.topic_brief_generation import create_topic_scope
from paper_reviewer.models.topic_brief_generation.reference import (
    Reference,
    create_reference,
    list_references_for_scope,
)
from paper_reviewer.topic_brief_generation.add_reference import (
    AddReferenceError,
    add_references,
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


def _reference_paper_ids(session: Session, topic_scope_id: int) -> list[int]:
    return [paper.id for _ref, paper in list_references_for_scope(session, topic_scope_id)]


def test_add_references_is_public() -> None:
    assert callable(add_references)


def test_add_references_empty_dois_is_noop(session: Session) -> None:
    topic_scope = create_topic_scope(session, "empty attach")
    session.flush()

    add_references(session, topic_scope, [])
    session.flush()

    assert list_references_for_scope(session, topic_scope.id) == []


def test_add_references_attaches_paper_by_doi(session: Session) -> None:
    topic_scope = create_topic_scope(session, "one attach")
    session.flush()
    paper_id = _add_paper(
        session, doi="10.1000/A", source_uid="1", title="Paper A"
    )

    add_references(session, topic_scope, ["10.1000/A"])
    session.flush()

    assert _reference_paper_ids(session, topic_scope.id) == [paper_id]


def test_add_references_normalizes_doi_case(session: Session) -> None:
    topic_scope = create_topic_scope(session, "doi case")
    session.flush()
    paper_id = _add_paper(
        session, doi="10.1000/A", source_uid="2", title="Paper A"
    )

    add_references(session, topic_scope, ["  10.1000/a  "])
    session.flush()

    assert _reference_paper_ids(session, topic_scope.id) == [paper_id]


def test_add_references_skips_existing_reference(session: Session) -> None:
    topic_scope = create_topic_scope(session, "already referenced")
    session.flush()
    paper_id = _add_paper(
        session, doi="10.1000/B", source_uid="3", title="Paper B"
    )
    create_reference(session, topic_scope.id, paper_id)
    session.flush()

    add_references(session, topic_scope, ["10.1000/B"])
    session.flush()

    rows = session.scalars(
        select(Reference).where(Reference.topic_scope_id == topic_scope.id)
    ).all()
    assert len(rows) == 1
    assert rows[0].paper_id == paper_id


def test_add_references_raises_when_paper_missing(session: Session) -> None:
    topic_scope = create_topic_scope(session, "missing paper")
    session.flush()

    with pytest.raises(AddReferenceError):
        add_references(session, topic_scope, ["10.1000/MISSING"])

    assert list_references_for_scope(session, topic_scope.id) == []


def test_add_references_raises_when_doi_blank(session: Session) -> None:
    topic_scope = create_topic_scope(session, "blank doi")
    session.flush()

    with pytest.raises(AddReferenceError):
        add_references(session, topic_scope, ["   "])

    assert list_references_for_scope(session, topic_scope.id) == []
