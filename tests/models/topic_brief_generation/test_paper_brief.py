"""PaperBrief ORM: unique paper_id, default status, content round-trip."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.topic_brief_generation import create_paper
from paper_reviewer.models.topic_brief_generation.paper_brief import (
    PaperBrief,
    create_paper_brief_row,
    get_paper_brief_by_paper_id,
)
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_brief_generation.generate_paper_brief import (
    PaperBriefContent,
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


def _paper(session: Session, *, uid: str = "1", doi: str = "10.1000/A") -> int:
    paper = create_paper(
        session,
        doi=doi,
        source_id="pubmed",
        source_uid=uid,
        title="Title",
        authors=[],
        url="https://example.com/a",
    )
    session.flush()
    return paper.id


def test_create_paper_brief_defaults_not_started(session: Session) -> None:
    paper_id = _paper(session)
    brief = create_paper_brief_row(session, paper_id=paper_id)
    session.flush()

    assert isinstance(brief, PaperBrief)
    assert brief.paper_id == paper_id
    assert brief.status is PaperAspectStatus.not_started
    assert brief.error_message is None
    assert brief.content is None
    assert brief.created_at is not None


def test_get_paper_brief_by_paper_id(session: Session) -> None:
    paper_id = _paper(session)
    created = create_paper_brief_row(session, paper_id=paper_id)
    session.flush()

    found = get_paper_brief_by_paper_id(session, paper_id)

    assert found is not None
    assert found.id == created.id


def test_paper_id_must_be_unique(session: Session) -> None:
    paper_id = _paper(session)
    create_paper_brief_row(session, paper_id=paper_id)
    session.flush()
    create_paper_brief_row(session, paper_id=paper_id)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_content_round_trip(session: Session) -> None:
    paper_id = _paper(session)
    brief = create_paper_brief_row(session, paper_id=paper_id)
    payload = PaperBriefContent(
        summary="Takeaway.",
        objective="Goal.",
        key_findings=["One"],
        limitations="Small sample.",
    )
    brief.content = payload.model_dump(mode="json")
    brief.status = PaperAspectStatus.succeeded
    session.flush()

    found = get_paper_brief_by_paper_id(session, paper_id)
    assert found is not None
    assert found.content is not None
    loaded = PaperBriefContent.model_validate(found.content)
    assert loaded.summary == "Takeaway."
    assert loaded.limitations == "Small sample."
    assert "relevance_to_topic" not in found.content
