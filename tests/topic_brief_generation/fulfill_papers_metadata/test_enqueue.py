"""Enqueue selection rules for fulfill papers metadata."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.paper import create_paper
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.topic_brief_generation.fulfill_papers_metadata import (
    enqueue_fulfill_papers_metadata,
    needs_fulfill_paper_metadata,
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    import paper_reviewer.models.paper  # noqa: F401

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


def test_needs_fulfill_when_source_not_started() -> None:
    assert (
        needs_fulfill_paper_metadata(
            PaperAspectStatus.not_started,
            PaperAspectStatus.not_started,
        )
        is True
    )


def test_needs_fulfill_when_source_succeeded_and_full_text_not_started() -> None:
    assert (
        needs_fulfill_paper_metadata(
            PaperAspectStatus.succeeded,
            PaperAspectStatus.not_started,
        )
        is True
    )


def test_needs_fulfill_false_when_both_terminal() -> None:
    assert (
        needs_fulfill_paper_metadata(
            PaperAspectStatus.succeeded,
            PaperAspectStatus.unavailable,
        )
        is False
    )
    assert (
        needs_fulfill_paper_metadata(
            PaperAspectStatus.failed,
            PaperAspectStatus.not_started,
        )
        is False
    )
    assert (
        needs_fulfill_paper_metadata(
            PaperAspectStatus.unavailable,
            PaperAspectStatus.not_started,
        )
        is False
    )


def test_enqueue_empty_paper_list(session: Session) -> None:
    submitted: list[tuple[int, str]] = []

    result = enqueue_fulfill_papers_metadata(
        session,
        [],
        submit_fulfill=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == []
    assert result.skipped_already_terminal == []
    assert submitted == []


def test_enqueue_skips_terminal_and_submits_pending_and_backfill(
    session: Session,
) -> None:
    id_pending = _create(session, uid="1", doi="10.1000/A")
    id_both_terminal = _create(
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
    id_backfill = _create(
        session,
        uid="5",
        doi="10.1000/E",
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.not_started,
    )
    submitted: list[tuple[int, str]] = []

    result = enqueue_fulfill_papers_metadata(
        session,
        [id_pending, id_both_terminal, id_failed, id_unavailable, id_backfill],
        submit_fulfill=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == [id_pending, id_backfill]
    assert result.skipped_already_terminal == [
        id_both_terminal,
        id_failed,
        id_unavailable,
    ]
    assert submitted == [(id_pending, "10.1000/A"), (id_backfill, "10.1000/E")]


def test_enqueue_spec_example_skips_both_terminal_submits_backfill(
    session: Session,
) -> None:
    id_pending = _create(session, uid="10", doi="10.1000/TEN")
    id_terminal = _create(
        session,
        uid="11",
        doi="10.1000/ELEVEN",
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.succeeded,
    )
    id_backfill = _create(
        session,
        uid="12",
        doi="10.1000/TWELVE",
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.not_started,
    )
    submitted: list[tuple[int, str]] = []

    result = enqueue_fulfill_papers_metadata(
        session,
        [id_pending, id_terminal, id_backfill],
        submit_fulfill=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == [id_pending, id_backfill]
    assert result.skipped_already_terminal == [id_terminal]
    assert submitted == [
        (id_pending, "10.1000/TEN"),
        (id_backfill, "10.1000/TWELVE"),
    ]


def test_enqueue_preserves_first_seen_order(session: Session) -> None:
    id_a = _create(session, uid="10", doi="10.1000/X")
    id_b = _create(session, uid="11", doi="10.1000/Y")
    submitted: list[tuple[int, str]] = []

    result = enqueue_fulfill_papers_metadata(
        session,
        [id_b, id_a],
        submit_fulfill=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == [id_b, id_a]
    assert submitted == [(id_b, "10.1000/Y"), (id_a, "10.1000/X")]


def test_enqueue_drops_missing_paper_ids(session: Session) -> None:
    id_pending = _create(session, uid="1", doi="10.1000/A")
    submitted: list[tuple[int, str]] = []

    result = enqueue_fulfill_papers_metadata(
        session,
        [id_pending, 999_999],
        submit_fulfill=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == [id_pending]
    assert result.skipped_already_terminal == []
    assert submitted == [(id_pending, "10.1000/A")]
