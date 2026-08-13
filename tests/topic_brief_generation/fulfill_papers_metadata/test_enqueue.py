"""Enqueue selection rules for fulfill papers metadata."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.topic_brief_generation import create_paper
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.topic_brief_generation.fulfill_papers_metadata import (
    enqueue_fulfill_papers_metadata,
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    import paper_reviewer.models.topic_brief_generation.paper  # noqa: F401

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


def _create(
    session: Session,
    *,
    uid: str,
    doi: str,
    source_record_status: PaperAspectStatus = PaperAspectStatus.not_started,
    full_text_status: PaperAspectStatus = PaperAspectStatus.not_started,
) -> int:
    paper = create_paper(
        session,
        doi=doi,
        source_id="pubmed",
        source_uid=uid,
        title=f"Title {uid}",
        authors=[],
        url=f"https://example.com/{uid}",
    )
    paper.source_record_status = source_record_status
    paper.full_text_status = full_text_status
    session.flush()
    return paper.id


def test_enqueue_empty_paper_list(session: Session) -> None:
    submitted: list[tuple[int, str]] = []

    result = enqueue_fulfill_papers_metadata(
        session,
        [],
        submit_inform=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == []
    assert result.skipped_already_informed == []
    assert result.skipped_already_failed == []
    assert submitted == []


def test_enqueue_skips_informed_and_failed_submits_rest(session: Session) -> None:
    id_pending = _create(session, uid="1", doi="10.1000/A")
    id_informed = _create(
        session,
        uid="2",
        doi="10.1000/B",
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.unavailable,
    )
    id_failed = _create(
        session,
        uid="3",
        doi="10.1000/C",
        source_record_status=PaperAspectStatus.failed,
    )
    id_unavailable = _create(
        session,
        uid="4",
        doi="10.1000/D",
        source_record_status=PaperAspectStatus.unavailable,
    )
    submitted: list[tuple[int, str]] = []

    result = enqueue_fulfill_papers_metadata(
        session,
        [id_pending, id_informed, id_failed, id_unavailable],
        submit_inform=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == [id_pending]
    assert result.skipped_already_informed == [id_informed]
    assert result.skipped_already_failed == [id_failed, id_unavailable]
    assert submitted == [(id_pending, "10.1000/A")]


def test_enqueue_preserves_first_seen_order(session: Session) -> None:
    id_a = _create(session, uid="10", doi="10.1000/X")
    id_b = _create(session, uid="11", doi="10.1000/Y")
    submitted: list[tuple[int, str]] = []

    result = enqueue_fulfill_papers_metadata(
        session,
        [id_b, id_a],
        submit_inform=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == [id_b, id_a]
    assert submitted == [(id_b, "10.1000/Y"), (id_a, "10.1000/X")]
