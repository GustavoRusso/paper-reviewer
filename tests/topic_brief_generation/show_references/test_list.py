"""list_show_references: map joined Reference rows to the list contract."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.paper import create_paper
from paper_reviewer.models.topic_brief_generation import create_topic_scope
from paper_reviewer.models.topic_brief_generation.reference import create_reference
from paper_reviewer.schemas.topic_brief_generation.show_references import (
    ShowReferencesResult,
)
from paper_reviewer.topic_brief_generation.show_references import (
    list_show_references,
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
    authors: list[str] | None = None,
    journal: str | None = "Nature",
    published_year: int | None = 2024,
) -> int:
    paper = create_paper(
        session,
        doi=doi,
        source_id="pubmed",
        source_uid=source_uid,
        title=title,
        authors=authors if authors is not None else ["Ada Lovelace"],
        url=f"https://example.com/{source_uid}",
        journal=journal,
        published_year=published_year,
    )
    session.flush()
    return paper.id


def test_list_show_references_empty_when_scope_has_none(session: Session) -> None:
    topic_scope = create_topic_scope(session, "no references yet")
    session.flush()

    result = list_show_references(session, topic_scope)

    assert isinstance(result, ShowReferencesResult)
    assert result.papers == []


def test_list_show_references_maps_bibliographic_fields(
    session: Session,
) -> None:
    topic_scope = create_topic_scope(session, "one reference")
    session.flush()
    paper_id = _add_paper(
        session,
        doi="10.1000/MAP",
        source_uid="41",
        title="Mapped paper",
        authors=["Ada Lovelace", "Alan Turing"],
        journal="Cell",
        published_year=2023,
    )
    attached_at = datetime(2026, 3, 4, tzinfo=UTC)
    row = create_reference(session, topic_scope.id, paper_id)
    row.created_at = attached_at
    session.flush()

    result = list_show_references(session, topic_scope)

    assert len(result.papers) == 1
    paper = result.papers[0]
    assert paper.title == "Mapped paper"
    assert paper.url == "https://example.com/41"
    assert paper.doi == "10.1000/MAP"
    assert paper.authors == ["Ada Lovelace", "Alan Turing"]
    assert paper.journal == "Cell"
    assert paper.published_year == 2023
    assert paper.referenced_at == attached_at


def test_list_show_references_orders_by_referenced_at(
    session: Session,
) -> None:
    topic_scope = create_topic_scope(session, "ordered references")
    session.flush()
    first_id = _add_paper(
        session, doi="10.1000/EARLY", source_uid="50", title="Early"
    )
    second_id = _add_paper(
        session, doi="10.1000/LATE", source_uid="51", title="Late"
    )
    create_reference(session, topic_scope.id, second_id).created_at = datetime(
        2026, 5, 2, tzinfo=UTC
    )
    create_reference(session, topic_scope.id, first_id).created_at = datetime(
        2026, 5, 1, tzinfo=UTC
    )
    session.flush()

    result = list_show_references(session, topic_scope)

    assert [paper.title for paper in result.papers] == ["Early", "Late"]
