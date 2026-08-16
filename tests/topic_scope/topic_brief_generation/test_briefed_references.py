"""Briefed Reference selection, citation_description, and prompt order."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.paper import create_paper
from paper_reviewer.models.paper_brief import create_paper_brief_row
from paper_reviewer.models.topic_scope import create_topic_scope
from paper_reviewer.models.topic_scope.reference import create_reference
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.topic_scope.topic_brief_generation import (
    citation_description,
    count_briefed_references,
    list_briefed_references,
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    import paper_reviewer.models.paper  # noqa: F401
    import paper_reviewer.models.paper_brief  # noqa: F401
    import paper_reviewer.models.topic_scope.reference  # noqa: F401
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


def _add_paper(
    session: Session,
    *,
    doi: str,
    source_uid: str,
    title: str,
    pub_date: date | None = None,
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
    paper.pub_date = pub_date
    session.flush()
    return paper.id


def test_citation_description_uppercases_doi() -> None:
    assert (
        citation_description(doi="10.1000/abc", title="A title")
        == "10.1000/ABC — A title"
    )


def test_count_briefed_references_is_zero_when_scope_has_no_references(
    session: Session,
) -> None:
    topic_scope = create_topic_scope(session, "empty scope")
    session.flush()

    assert count_briefed_references(session, topic_scope.id) == 0


def test_count_briefed_references_excludes_missing_and_non_succeeded_briefs(
    session: Session,
) -> None:
    topic_scope = create_topic_scope(session, "mixed briefs")
    session.flush()
    succeeded_id = _add_paper(
        session, doi="10.1000/OK", source_uid="1", title="Ok"
    )
    failed_id = _add_paper(
        session, doi="10.1000/FAIL", source_uid="2", title="Fail"
    )
    none_id = _add_paper(
        session, doi="10.1000/NONE", source_uid="3", title="None"
    )
    not_started_id = _add_paper(
        session, doi="10.1000/NS", source_uid="4", title="NS"
    )
    create_reference(session, topic_scope.id, succeeded_id)
    create_reference(session, topic_scope.id, failed_id)
    create_reference(session, topic_scope.id, none_id)
    create_reference(session, topic_scope.id, not_started_id)
    create_paper_brief_row(
        session, paper_id=succeeded_id, status=PaperAspectStatus.succeeded
    )
    create_paper_brief_row(
        session, paper_id=failed_id, status=PaperAspectStatus.failed
    )
    create_paper_brief_row(
        session, paper_id=not_started_id, status=PaperAspectStatus.not_started
    )
    session.flush()

    assert count_briefed_references(session, topic_scope.id) == 1


def test_count_briefed_references_excludes_other_topic_scopes(
    session: Session,
) -> None:
    scope_a = create_topic_scope(session, "scope a")
    scope_b = create_topic_scope(session, "scope b")
    session.flush()
    paper_id = _add_paper(
        session, doi="10.1000/SHARED", source_uid="10", title="Shared"
    )
    create_reference(session, scope_b.id, paper_id)
    create_paper_brief_row(
        session, paper_id=paper_id, status=PaperAspectStatus.succeeded
    )
    session.flush()

    assert count_briefed_references(session, scope_a.id) == 0
    assert count_briefed_references(session, scope_b.id) == 1


def test_list_briefed_references_orders_by_pub_date_desc_nulls_last(
    session: Session,
) -> None:
    topic_scope = create_topic_scope(session, "order")
    session.flush()
    older_id = _add_paper(
        session,
        doi="10.1000/old",
        source_uid="1",
        title="Older",
        pub_date=date(2020, 1, 1),
    )
    newer_id = _add_paper(
        session,
        doi="10.1000/new",
        source_uid="2",
        title="Newer",
        pub_date=date(2024, 1, 1),
    )
    null_id = _add_paper(
        session,
        doi="10.1000/null",
        source_uid="3",
        title="Null date",
        pub_date=None,
    )
    later = datetime(2026, 1, 2, tzinfo=UTC)
    earlier = datetime(2026, 1, 1, tzinfo=UTC)
    create_reference(session, topic_scope.id, older_id).created_at = later
    create_reference(session, topic_scope.id, newer_id).created_at = earlier
    create_reference(session, topic_scope.id, null_id).created_at = later
    for paper_id in (older_id, newer_id, null_id):
        create_paper_brief_row(
            session, paper_id=paper_id, status=PaperAspectStatus.succeeded
        )
    session.flush()

    listed = list_briefed_references(session, topic_scope.id)

    assert [item.title for item in listed] == ["Newer", "Older", "Null date"]
    assert listed[0].citation_description == "10.1000/NEW — Newer"


def test_list_briefed_references_tie_breaks_by_created_at_then_id(
    session: Session,
) -> None:
    topic_scope = create_topic_scope(session, "ties")
    session.flush()
    first_id = _add_paper(
        session,
        doi="10.1000/a",
        source_uid="10",
        title="A",
        pub_date=date(2024, 1, 1),
    )
    second_id = _add_paper(
        session,
        doi="10.1000/b",
        source_uid="11",
        title="B",
        pub_date=date(2024, 1, 1),
    )
    same_day = datetime(2026, 1, 1, tzinfo=UTC)
    create_reference(session, topic_scope.id, first_id).created_at = same_day
    create_reference(session, topic_scope.id, second_id).created_at = same_day
    for paper_id in (first_id, second_id):
        create_paper_brief_row(
            session, paper_id=paper_id, status=PaperAspectStatus.succeeded
        )
    session.flush()

    listed = list_briefed_references(session, topic_scope.id)

    assert [item.title for item in listed] == ["A", "B"]
    assert listed[0].reference_id < listed[1].reference_id
