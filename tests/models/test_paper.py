"""Paper ORM: create and look up by source handle or DOI."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Computed, create_engine, insert
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateTable

from paper_reviewer.models.base import Base
from paper_reviewer.models.paper import (
    Paper,
    create_paper,
    get_paper_by_doi,
    get_paper_by_id,
    get_paper_by_source_handle,
)

_KEYWORDS_TSV_GENERATOR_PARTS = (
    "jsonb_to_tsvector('simple'",
    "coalesce(source_record->'indexing'->'keywords', '[]'::jsonb)",
    r'[\"string\"]',
)
_ALEMBIC_KEYWORDS_TSV = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "20260816_0012_paper_keywords_tsv.py"
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


def test_keywords_tsv_is_mapped_nullable_without_computed(
    session: Session,
) -> None:
    paper = create_paper(
        session,
        doi="10.1000/KEYWORDS",
        source_id="pubmed",
        source_uid="33",
        title="Keywords mapping",
        authors=[],
        url="https://example.com/keywords",
    )
    session.flush()

    column = Paper.__table__.c.keywords_tsv
    assert column.nullable is True
    assert not isinstance(column.server_default, Computed)
    assert paper.keywords_tsv is None


def test_keywords_tsv_orm_create_table_has_no_jsonb_to_tsvector() -> None:
    ddl = str(CreateTable(Paper.__table__).compile(dialect=postgresql.dialect()))

    assert "keywords_tsv" in ddl
    assert "jsonb_to_tsvector" not in ddl
    assert "GENERATED" not in ddl.upper()


def test_keywords_tsv_gin_index_is_declared() -> None:
    indexes = {index.name: index for index in Paper.__table__.indexes}
    gin = indexes["ix_papers_keywords_tsv"]

    assert list(gin.columns.keys()) == ["keywords_tsv"]
    assert gin.dialect_options["postgresql"]["using"] == "gin"


def test_paper_insert_omits_keywords_tsv() -> None:
    stmt = insert(Paper).values(
        doi="10.1000/INSERT",
        source_id="pubmed",
        source_uid="22",
        title="Insert omit",
        authors=[],
        url="https://example.com/insert",
    )
    compiled = str(stmt.compile(dialect=postgresql.dialect()))

    assert "keywords_tsv" not in compiled


def test_alembic_keywords_tsv_migration_owns_generator_and_gin() -> None:
    source = _ALEMBIC_KEYWORDS_TSV.read_text(encoding="utf-8")

    for part in _KEYWORDS_TSV_GENERATOR_PARTS:
        assert part in source
    assert "ix_papers_keywords_tsv" in source
    assert "postgresql_using=\"gin\"" in source or "postgresql_using='gin'" in source
    assert "persisted=True" in source or "STORED" in source.upper()
