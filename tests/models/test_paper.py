"""Paper ORM: create and look up by source handle or DOI."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.paper import (
    Paper,
    create_paper,
    get_paper_by_doi,
    get_paper_by_id,
    get_paper_by_source_handle,
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    # Register mapped tables before create_all.
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


def test_create_paper_stores_fields_and_ids(session: Session) -> None:
    paper = create_paper(
        session,
        doi="10.1000/EXAMPLE",
        source_id="pubmed",
        source_uid="12345",
        title="Example title",
        authors=["Ada Lovelace", "Alan Turing"],
        url="https://pubmed.ncbi.nlm.nih.gov/12345/",
        journal="Nature",
        published_year=2024,
    )
    session.flush()

    assert isinstance(paper, Paper)
    assert isinstance(paper.id, int)
    assert paper.id > 0
    assert paper.doi == "10.1000/EXAMPLE"
    assert paper.source_id == "pubmed"
    assert paper.source_uid == "12345"
    assert paper.title == "Example title"
    assert paper.authors == ["Ada Lovelace", "Alan Turing"]
    assert paper.journal == "Nature"
    assert paper.published_year == 2024
    assert paper.url == "https://pubmed.ncbi.nlm.nih.gov/12345/"
    assert paper.created_at is not None


def test_get_paper_by_source_handle(session: Session) -> None:
    created = create_paper(
        session,
        doi="10.1000/A",
        source_id="pubmed",
        source_uid="99",
        title="Title A",
        authors=[],
        url="https://example.com/a",
    )
    session.flush()

    found = get_paper_by_source_handle(session, "pubmed", "99")

    assert found is not None
    assert found.id == created.id


def test_get_paper_by_source_handle_returns_none_when_missing(
    session: Session,
) -> None:
    found = get_paper_by_source_handle(session, "pubmed", "missing")

    assert found is None


def test_get_paper_by_doi(session: Session) -> None:
    created = create_paper(
        session,
        doi="10.1000/B",
        source_id="pubmed",
        source_uid="88",
        title="Title B",
        authors=[],
        url="https://example.com/b",
    )
    session.flush()

    found = get_paper_by_doi(session, "10.1000/B")

    assert found is not None
    assert found.id == created.id


def test_get_paper_by_doi_returns_none_when_missing(session: Session) -> None:
    found = get_paper_by_doi(session, "10.1000/MISSING")

    assert found is None


def test_get_paper_by_id(session: Session) -> None:
    created = create_paper(
        session,
        doi="10.1000/BYID",
        source_id="pubmed",
        source_uid="55",
        title="By id",
        authors=[],
        url="https://example.com/byid",
    )
    session.flush()

    found = get_paper_by_id(session, created.id)

    assert found is not None
    assert found.id == created.id


def test_get_paper_by_id_returns_none_when_missing(session: Session) -> None:
    found = get_paper_by_id(session, 999_999)

    assert found is None


def test_paper_inform_columns_default_not_started(session: Session) -> None:
    paper = create_paper(
        session,
        doi="10.1000/INFORM",
        source_id="pubmed",
        source_uid="44",
        title="Inform defaults",
        authors=[],
        url="https://example.com/inform",
    )
    session.flush()

    assert paper.source_record is None
    assert paper.source_record_status.value == "not_started"
    assert paper.full_text_status.value == "not_started"
    assert paper.source_record_error_message is None
    assert paper.full_text_error_message is None
    assert paper.pub_date is None
    assert paper.abstract_text is None
    assert paper.pmcid is None
    assert paper.pmcid_version is None
    assert paper.is_open_access is None
    assert paper.full_text_plain is None
    assert paper.open_access_pdf_url is None
    assert paper.pmc_article_url is None


def test_source_handle_must_be_unique(session: Session) -> None:
    create_paper(
        session,
        doi="10.1000/C1",
        source_id="pubmed",
        source_uid="77",
        title="First",
        authors=[],
        url="https://example.com/c1",
    )
    session.flush()

    create_paper(
        session,
        doi="10.1000/C2",
        source_id="pubmed",
        source_uid="77",
        title="Second",
        authors=[],
        url="https://example.com/c2",
    )
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_doi_must_be_unique(session: Session) -> None:
    create_paper(
        session,
        doi="10.1000/SAME",
        source_id="pubmed",
        source_uid="66",
        title="First",
        authors=[],
        url="https://example.com/d1",
    )
    session.flush()

    create_paper(
        session,
        doi="10.1000/SAME",
        source_id="pubmed",
        source_uid="65",
        title="Second",
        authors=[],
        url="https://example.com/d2",
    )
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()
