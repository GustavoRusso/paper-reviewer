"""Topic facet ORM: insert, reload, uniqueness."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.topic_scope import (
    TopicFacet,
    TopicScope,
    create_topic_scope,
    list_topic_facets_for_scope,
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


def _add_facet(
    session: Session,
    topic_scope: TopicScope,
    *,
    facet_id: str = "core-concepts",
    position: int = 0,
) -> TopicFacet:
    row = TopicFacet(
        topic_scope_id=topic_scope.id,
        facet_id=facet_id,
        label="Core concepts",
        intent="Narrow topical match from biomedical entities",
        concepts=["glioblastoma", "immunotherapy"],
        synonyms=["GBM"],
        date_from="2018-01-01",
        date_to=None,
        filters={"mesh_terms": ["Glioblastoma"]},
        retmax=50,
        position=position,
    )
    session.add(row)
    session.flush()
    return row


def test_topic_facet_round_trip_preserves_list_and_object_fields(
    session: Session,
) -> None:
    topic_scope = create_topic_scope(session, "glioblastoma immunotherapy")
    session.flush()
    created = _add_facet(session, topic_scope)
    session.refresh(created)

    loaded = session.scalar(select(TopicFacet).where(TopicFacet.id == created.id))

    assert loaded is not None
    assert loaded.topic_scope_id == topic_scope.id
    assert loaded.facet_id == "core-concepts"
    assert loaded.label == "Core concepts"
    assert loaded.intent == "Narrow topical match from biomedical entities"
    assert loaded.concepts == ["glioblastoma", "immunotherapy"]
    assert loaded.synonyms == ["GBM"]
    assert loaded.date_from == "2018-01-01"
    assert loaded.date_to is None
    assert loaded.filters == {"mesh_terms": ["Glioblastoma"]}
    assert loaded.retmax == 50
    assert loaded.position == 0
    assert loaded.id > 0
    assert loaded.created_at is not None


def test_list_topic_facets_for_scope_orders_by_position(session: Session) -> None:
    topic_scope = create_topic_scope(session, "two facets")
    session.flush()
    _add_facet(session, topic_scope, facet_id="later", position=1)
    _add_facet(session, topic_scope, facet_id="first", position=0)

    listed = list_topic_facets_for_scope(session, topic_scope.id)

    assert [row.facet_id for row in listed] == ["first", "later"]


def test_unique_topic_scope_id_and_facet_id(session: Session) -> None:
    topic_scope = create_topic_scope(session, "duplicate facet id")
    session.flush()
    _add_facet(session, topic_scope, facet_id="core-concepts")

    session.add(
        TopicFacet(
            topic_scope_id=topic_scope.id,
            facet_id="core-concepts",
            label="Dup",
            concepts=["x"],
            synonyms=[],
            filters={},
            position=1,
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()
