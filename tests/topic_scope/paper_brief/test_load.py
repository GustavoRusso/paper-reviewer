"""load_paper_brief_for_read: succeeded brief by DOI."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.paper import create_paper
from paper_reviewer.models.paper_brief import create_paper_brief_row
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    PaperBriefContent,
)
from paper_reviewer.schemas.topic_scope.paper_brief import (
    PaperBriefReadStatus,
)
from paper_reviewer.topic_scope.paper_brief import load_paper_brief_for_read
from tests.topic_scope.generate_paper_brief.helpers import sample_brief_content


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
    doi: str = "10.1000/EXAMPLE",
    source_uid: str = "100",
    title: str = "Example title",
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


def test_load_paper_brief_for_read_ready_when_succeeded(
    session: Session,
) -> None:
    paper_id = _add_paper(session)
    content = sample_brief_content(
        study_type="Cohort",
        key_findings=["Metric increased."],
    )
    row = create_paper_brief_row(
        session, paper_id=paper_id, status=PaperAspectStatus.succeeded
    )
    row.content = content.model_dump(mode="json")
    session.flush()

    result = load_paper_brief_for_read(session, "10.1000/EXAMPLE")

    assert result.status is PaperBriefReadStatus.ready
    assert result.doi == "10.1000/EXAMPLE"
    assert result.title == "Example title"
    assert result.url == "https://example.com/100"
    assert result.authors == ["Ada Lovelace"]
    assert result.journal == "Nature"
    assert result.published_year == 2024
    assert isinstance(result.content, PaperBriefContent)
    assert result.content.summary == content.summary
    assert result.content.study_type == "Cohort"
    assert result.content.key_findings == ["Metric increased."]


def test_load_paper_brief_for_read_paper_missing(session: Session) -> None:
    result = load_paper_brief_for_read(session, "10.1000/MISSING")

    assert result.status is PaperBriefReadStatus.paper_missing
    assert result.doi == "10.1000/MISSING"
    assert result.title is None
    assert result.content is None


def test_load_paper_brief_for_read_unavailable_when_no_row(
    session: Session,
) -> None:
    _add_paper(session)

    result = load_paper_brief_for_read(session, "10.1000/EXAMPLE")

    assert result.status is PaperBriefReadStatus.brief_unavailable
    assert result.title == "Example title"
    assert result.content is None


def test_load_paper_brief_for_read_unavailable_when_failed(
    session: Session,
) -> None:
    paper_id = _add_paper(session)
    create_paper_brief_row(
        session, paper_id=paper_id, status=PaperAspectStatus.failed
    )
    session.flush()

    result = load_paper_brief_for_read(session, "10.1000/EXAMPLE")

    assert result.status is PaperBriefReadStatus.brief_unavailable
    assert result.content is None


def test_load_paper_brief_for_read_invalid_when_succeeded_json_bad(
    session: Session,
) -> None:
    paper_id = _add_paper(session)
    row = create_paper_brief_row(
        session, paper_id=paper_id, status=PaperAspectStatus.succeeded
    )
    row.content = {"summary": "Only summary."}
    session.flush()

    result = load_paper_brief_for_read(session, "10.1000/EXAMPLE")

    assert result.status is PaperBriefReadStatus.invalid_content
    assert result.title == "Example title"
    assert result.content is None


def test_load_paper_brief_for_read_invalid_when_succeeded_content_missing(
    session: Session,
) -> None:
    paper_id = _add_paper(session)
    create_paper_brief_row(
        session, paper_id=paper_id, status=PaperAspectStatus.succeeded
    )
    session.flush()

    result = load_paper_brief_for_read(session, "10.1000/EXAMPLE")

    assert result.status is PaperBriefReadStatus.invalid_content
    assert result.content is None
