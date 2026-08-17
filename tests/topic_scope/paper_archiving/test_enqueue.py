"""Enqueue selection for regenerate_paper after paper archiving."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.paper import create_paper
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.paper_archiving import (
    Paper,
    PaperArchivingResult,
)
from paper_reviewer.topic_scope.paper_archiving import enqueue_regenerate_papers


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


def _read_paper(
    session: Session,
    *,
    uid: str,
    doi: str,
    source_record_status: PaperAspectStatus = PaperAspectStatus.not_started,
    full_text_status: PaperAspectStatus = PaperAspectStatus.not_started,
) -> Paper:
    row = create_paper(
        session,
        doi=doi,
        source_id="pubmed",
        source_uid=uid,
        title=f"Title {uid}",
        authors=[],
        url=f"https://example.com/{uid}",
    )
    row.source_record_status = source_record_status
    row.full_text_status = full_text_status
    session.flush()
    return Paper(
        id=row.id,
        created_at=row.created_at or datetime.now(UTC),
        doi=row.doi,
        source_id=row.source_id,
        source_uid=row.source_uid,
        title=row.title,
        authors=list(row.authors),
        journal=row.journal,
        published_year=row.published_year,
        url=row.url,
    )


def test_enqueue_empty_papers(session: Session) -> None:
    submitted: list[tuple[int, str]] = []

    result = enqueue_regenerate_papers(
        session,
        PaperArchivingResult(),
        submit_regenerate=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == []
    assert result.skipped_already_existed == []
    assert submitted == []


def test_enqueue_submits_created_ids(session: Session) -> None:
    created = _read_paper(session, uid="1", doi="10.1000/A")
    submitted: list[tuple[int, str]] = []

    result = enqueue_regenerate_papers(
        session,
        PaperArchivingResult(papers=[created], created_paper_ids=[created.id]),
        submit_regenerate=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == [created.id]
    assert result.skipped_already_existed == []
    assert submitted == [(created.id, "10.1000/A")]


def test_enqueue_skips_reused_terminal_paper(session: Session) -> None:
    reused = _read_paper(
        session,
        uid="1",
        doi="10.1000/A",
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.succeeded,
    )
    submitted: list[tuple[int, str]] = []

    result = enqueue_regenerate_papers(
        session,
        PaperArchivingResult(papers=[reused], created_paper_ids=[]),
        submit_regenerate=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == []
    assert result.skipped_already_existed == [reused.id]
    assert submitted == []


def test_enqueue_submits_reused_not_started(session: Session) -> None:
    reused = _read_paper(session, uid="1", doi="10.1000/A")
    submitted: list[tuple[int, str]] = []

    result = enqueue_regenerate_papers(
        session,
        PaperArchivingResult(papers=[reused], created_paper_ids=[]),
        submit_regenerate=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == [reused.id]
    assert result.skipped_already_existed == []
    assert submitted == [(reused.id, "10.1000/A")]


def test_enqueue_mixed_created_reused_and_not_started(session: Session) -> None:
    created = _read_paper(session, uid="1", doi="10.1000/A")
    reused_done = _read_paper(
        session,
        uid="2",
        doi="10.1000/B",
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.unavailable,
    )
    reused_stuck = _read_paper(session, uid="3", doi="10.1000/C")
    submitted: list[tuple[int, str]] = []

    result = enqueue_regenerate_papers(
        session,
        PaperArchivingResult(
            papers=[created, reused_done, reused_stuck],
            created_paper_ids=[created.id],
        ),
        submit_regenerate=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == [created.id, reused_stuck.id]
    assert result.skipped_already_existed == [reused_done.id]
    assert submitted == [(created.id, "10.1000/A"), (reused_stuck.id, "10.1000/C")]


def test_enqueue_drops_missing_paper_ids(session: Session) -> None:
    created = _read_paper(session, uid="1", doi="10.1000/A")
    missing = Paper(
        id=999_999,
        created_at=datetime.now(UTC),
        doi="10.1000/MISSING",
        source_id="pubmed",
        source_uid="999",
        title="Missing",
        url="https://example.com/missing",
    )
    submitted: list[tuple[int, str]] = []

    result = enqueue_regenerate_papers(
        session,
        PaperArchivingResult(
            papers=[created, missing],
            created_paper_ids=[created.id, missing.id],
        ),
        submit_regenerate=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == [created.id]
    assert result.skipped_already_existed == []
    assert submitted == [(created.id, "10.1000/A")]


def test_enqueue_does_not_submit_reused_failed_source(session: Session) -> None:
    reused = _read_paper(
        session,
        uid="1",
        doi="10.1000/A",
        source_record_status=PaperAspectStatus.failed,
        full_text_status=PaperAspectStatus.not_started,
    )
    submitted: list[tuple[int, str]] = []

    result = enqueue_regenerate_papers(
        session,
        PaperArchivingResult(papers=[reused], created_paper_ids=[]),
        submit_regenerate=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == []
    assert result.skipped_already_existed == [reused.id]
    assert submitted == []
