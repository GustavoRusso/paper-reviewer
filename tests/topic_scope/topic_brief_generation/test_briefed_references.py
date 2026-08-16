"""Briefed Reference selection for Topic brief generation."""

from __future__ import annotations

from collections.abc import Iterator

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
    count_briefed_references,
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


def _add_paper(session: Session, *, doi: str, source_uid: str) -> int:
    paper = create_paper(
        session,
        doi=doi,
        source_id="pubmed",
        source_uid=source_uid,
        title=f"Title {source_uid}",
        authors=["Ada Lovelace"],
        url=f"https://example.com/{source_uid}",
        journal="Nature",
        published_year=2024,
    )
    session.flush()
    return paper.id


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
    succeeded_id = _add_paper(session, doi="10.1000/OK", source_uid="1")
    failed_id = _add_paper(session, doi="10.1000/FAIL", source_uid="2")
    none_id = _add_paper(session, doi="10.1000/NONE", source_uid="3")
    not_started_id = _add_paper(session, doi="10.1000/NS", source_uid="4")
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
    paper_id = _add_paper(session, doi="10.1000/SHARED", source_uid="10")
    create_reference(session, scope_b.id, paper_id)
    create_paper_brief_row(
        session, paper_id=paper_id, status=PaperAspectStatus.succeeded
    )
    session.flush()

    assert count_briefed_references(session, scope_a.id) == 0
    assert count_briefed_references(session, scope_b.id) == 1


def test_count_briefed_references_counts_all_succeeded_on_scope(
    session: Session,
) -> None:
    topic_scope = create_topic_scope(session, "two briefed")
    session.flush()
    first_id = _add_paper(session, doi="10.1000/A", source_uid="20")
    second_id = _add_paper(session, doi="10.1000/B", source_uid="21")
    create_reference(session, topic_scope.id, first_id)
    create_reference(session, topic_scope.id, second_id)
    create_paper_brief_row(
        session, paper_id=first_id, status=PaperAspectStatus.succeeded
    )
    create_paper_brief_row(
        session, paper_id=second_id, status=PaperAspectStatus.succeeded
    )
    session.flush()

    assert count_briefed_references(session, topic_scope.id) == 2
