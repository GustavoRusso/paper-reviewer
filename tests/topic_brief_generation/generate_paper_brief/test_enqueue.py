"""Enqueue selection rules for generate paper brief."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.topic_brief_generation import create_paper
from paper_reviewer.models.topic_brief_generation.paper_brief import create_paper_brief_row
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.topic_brief_generation.generate_paper_brief import (
    enqueue_generate_paper_briefs,
    needs_create_paper_brief,
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    import paper_reviewer.models.topic_brief_generation.paper  # noqa: F401
    import paper_reviewer.models.topic_brief_generation.paper_brief  # noqa: F401

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


def _create_paper(
    session: Session,
    *,
    uid: str,
    doi: str,
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
    paper.full_text_status = full_text_status
    if full_text_status is PaperAspectStatus.succeeded:
        paper.full_text_plain = "Full article text."
    session.flush()
    return paper.id


def test_needs_create_when_full_text_succeeded_and_no_brief() -> None:
    assert (
        needs_create_paper_brief(PaperAspectStatus.succeeded, None) is True
    )


def test_needs_create_when_full_text_succeeded_and_brief_not_started() -> None:
    assert (
        needs_create_paper_brief(
            PaperAspectStatus.succeeded,
            PaperAspectStatus.not_started,
        )
        is True
    )


def test_needs_create_false_when_full_text_not_succeeded() -> None:
    assert needs_create_paper_brief(PaperAspectStatus.not_started, None) is False
    assert needs_create_paper_brief(PaperAspectStatus.unavailable, None) is False
    assert needs_create_paper_brief(PaperAspectStatus.failed, None) is False


def test_needs_create_false_when_brief_terminal() -> None:
    assert (
        needs_create_paper_brief(
            PaperAspectStatus.succeeded,
            PaperAspectStatus.succeeded,
        )
        is False
    )
    assert (
        needs_create_paper_brief(
            PaperAspectStatus.succeeded,
            PaperAspectStatus.failed,
        )
        is False
    )


def test_enqueue_empty_paper_list(session: Session) -> None:
    submitted: list[tuple[int, str]] = []

    result = enqueue_generate_paper_briefs(
        session,
        [],
        submit_brief=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == []
    assert result.skipped_already_terminal == []
    assert submitted == []


def test_enqueue_skips_blocked_and_succeeded_submits_needed(
    session: Session,
) -> None:
    id_needed = _create_paper(
        session,
        uid="1",
        doi="10.1000/A",
        full_text_status=PaperAspectStatus.succeeded,
    )
    id_succeeded_brief = _create_paper(
        session,
        uid="2",
        doi="10.1000/B",
        full_text_status=PaperAspectStatus.succeeded,
    )
    create_paper_brief_row(
        session,
        paper_id=id_succeeded_brief,
        status=PaperAspectStatus.succeeded,
    )
    id_blocked = _create_paper(
        session,
        uid="3",
        doi="10.1000/C",
        full_text_status=PaperAspectStatus.unavailable,
    )
    id_failed_brief = _create_paper(
        session,
        uid="4",
        doi="10.1000/D",
        full_text_status=PaperAspectStatus.succeeded,
    )
    create_paper_brief_row(
        session,
        paper_id=id_failed_brief,
        status=PaperAspectStatus.failed,
        error_message="prior",
    )
    session.flush()
    submitted: list[tuple[int, str]] = []

    result = enqueue_generate_paper_briefs(
        session,
        [id_needed, id_succeeded_brief, id_blocked, id_failed_brief],
        submit_brief=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == [id_needed]
    assert result.skipped_already_terminal == [
        id_succeeded_brief,
        id_blocked,
        id_failed_brief,
    ]
    assert submitted == [(id_needed, "10.1000/A")]


def test_enqueue_preserves_first_seen_order(session: Session) -> None:
    id_a = _create_paper(
        session,
        uid="10",
        doi="10.1000/X",
        full_text_status=PaperAspectStatus.succeeded,
    )
    id_b = _create_paper(
        session,
        uid="11",
        doi="10.1000/Y",
        full_text_status=PaperAspectStatus.succeeded,
    )
    submitted: list[tuple[int, str]] = []

    result = enqueue_generate_paper_briefs(
        session,
        [id_b, id_a],
        submit_brief=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == [id_b, id_a]
    assert submitted == [(id_b, "10.1000/Y"), (id_a, "10.1000/X")]


def test_enqueue_drops_missing_paper_ids(session: Session) -> None:
    id_needed = _create_paper(
        session,
        uid="1",
        doi="10.1000/A",
        full_text_status=PaperAspectStatus.succeeded,
    )
    submitted: list[tuple[int, str]] = []

    result = enqueue_generate_paper_briefs(
        session,
        [id_needed, 999_999],
        submit_brief=lambda paper_id, doi: submitted.append((paper_id, doi)),
    )

    assert result.submitted_paper_ids == [id_needed]
    assert result.skipped_already_terminal == []
    assert submitted == [(id_needed, "10.1000/A")]
