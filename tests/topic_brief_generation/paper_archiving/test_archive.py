"""Paper archiving: create-or-reuse Papers from candidates."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.paper import (
    create_paper,
    get_paper_by_doi,
    get_paper_by_source_handle,
)
from paper_reviewer.schemas.topic_brief_generation.paper_archiving import (
    ArchiveSkipReason,
)
from paper_reviewer.schemas.topic_brief_generation.search_external_sources import (
    PaperCandidate,
)
from paper_reviewer.topic_brief_generation.paper_archiving import archive_papers


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


def _candidate(**overrides: object) -> PaperCandidate:
    data: dict[str, object] = {
        "source_id": "pubmed",
        "source_uid": "100",
        "doi": "10.1000/example",
        "title": "Example title",
        "authors": ["Ada Lovelace"],
        "journal": "Nature",
        "published_year": 2024,
        "url": "https://pubmed.ncbi.nlm.nih.gov/100/",
        "snippet": "snippet text",
        "facet_id": "facet-1",
        "raw_payload_ref": "ref-1",
    }
    data.update(overrides)
    return PaperCandidate.model_validate(data)


def test_archive_papers_empty_list_returns_empty_success(session: Session) -> None:
    result = archive_papers(session, [])

    assert result.papers == []
    assert result.skipped == []
    assert result.errors == []


def test_archive_papers_inserts_new_identity_with_uppercase_doi(
    session: Session,
) -> None:
    result = archive_papers(session, [_candidate(doi="10.1000/MixedCase")])

    assert len(result.papers) == 1
    assert result.skipped == []
    assert result.errors == []
    paper = result.papers[0]
    assert paper.doi == "10.1000/MIXEDCASE"
    assert paper.source_id == "pubmed"
    assert paper.source_uid == "100"
    assert paper.title == "Example title"
    assert paper.authors == ["Ada Lovelace"]
    assert paper.url == "https://pubmed.ncbi.nlm.nih.gov/100/"
    assert paper.id > 0
    assert paper.created_at is not None

    stored = get_paper_by_source_handle(session, "pubmed", "100")
    assert stored is not None
    assert stored.doi == "10.1000/MIXEDCASE"


def test_archive_papers_reuses_existing_source_handle_without_field_updates(
    session: Session,
) -> None:
    create_paper(
        session,
        doi="10.1000/SAME",
        source_id="pubmed",
        source_uid="100",
        title="Original title",
        authors=["Original Author"],
        url="https://example.com/original",
        journal="Original Journal",
        published_year=2020,
    )
    session.flush()

    result = archive_papers(
        session,
        [
            _candidate(
                doi="10.1000/same",
                title="Updated title",
                authors=["New Author"],
                url="https://example.com/new",
                journal="New Journal",
                published_year=2025,
            )
        ],
    )

    assert len(result.papers) == 1
    paper = result.papers[0]
    assert paper.title == "Original title"
    assert paper.authors == ["Original Author"]
    assert paper.url == "https://example.com/original"
    assert paper.journal == "Original Journal"
    assert paper.published_year == 2020
    assert paper.doi == "10.1000/SAME"


def test_archive_papers_updates_doi_when_new_doi_is_free(session: Session) -> None:
    create_paper(
        session,
        doi="10.1000/A",
        source_id="pubmed",
        source_uid="100",
        title="Title",
        authors=[],
        url="https://example.com/a",
    )
    session.flush()

    result = archive_papers(session, [_candidate(doi="10.1000/b")])

    assert len(result.papers) == 1
    assert result.papers[0].doi == "10.1000/B"
    stored = get_paper_by_source_handle(session, "pubmed", "100")
    assert stored is not None
    assert stored.doi == "10.1000/B"
    assert get_paper_by_doi(session, "10.1000/A") is None


def test_archive_papers_skips_doi_update_when_new_doi_owned_elsewhere(
    session: Session,
) -> None:
    create_paper(
        session,
        doi="10.1000/A",
        source_id="pubmed",
        source_uid="100",
        title="Title A",
        authors=[],
        url="https://example.com/a",
    )
    create_paper(
        session,
        doi="10.1000/B",
        source_id="pubmed",
        source_uid="200",
        title="Title B",
        authors=[],
        url="https://example.com/b",
    )
    session.flush()

    result = archive_papers(
        session,
        [_candidate(source_uid="100", doi="10.1000/b")],
    )

    assert result.papers == []
    assert len(result.skipped) == 1
    assert result.skipped[0].reason == ArchiveSkipReason.doi_conflict
    assert result.skipped[0].source_uid == "100"
    stored = get_paper_by_source_handle(session, "pubmed", "100")
    assert stored is not None
    assert stored.doi == "10.1000/A"


def test_archive_papers_skips_new_row_when_doi_already_owned(
    session: Session,
) -> None:
    create_paper(
        session,
        doi="10.1000/TAKEN",
        source_id="pubmed",
        source_uid="200",
        title="Owner",
        authors=[],
        url="https://example.com/owner",
    )
    session.flush()

    result = archive_papers(
        session,
        [_candidate(source_uid="100", doi="10.1000/taken")],
    )

    assert result.papers == []
    assert len(result.skipped) == 1
    assert result.skipped[0].reason == ArchiveSkipReason.doi_conflict
    assert get_paper_by_source_handle(session, "pubmed", "100") is None


def test_archive_papers_skips_blank_doi(session: Session) -> None:
    result = archive_papers(
        session,
        [
            _candidate(doi=None, source_uid="1"),
            _candidate(doi="   ", source_uid="2"),
            _candidate(doi="10.1000/ok", source_uid="3"),
        ],
    )

    assert len(result.papers) == 1
    assert result.papers[0].source_uid == "3"
    assert len(result.skipped) == 2
    assert all(s.reason == ArchiveSkipReason.missing_doi for s in result.skipped)


def test_archive_papers_skips_blank_required_fields(session: Session) -> None:
    result = archive_papers(
        session,
        [
            _candidate(source_id="  ", source_uid="1"),
            _candidate(source_uid="  ", doi="10.1000/a"),
            _candidate(title="  ", source_uid="3", doi="10.1000/b"),
            _candidate(url="  ", source_uid="4", doi="10.1000/c"),
            _candidate(source_uid="5", doi="10.1000/d"),
        ],
    )

    assert len(result.papers) == 1
    assert result.papers[0].source_uid == "5"
    assert len(result.skipped) == 4
    assert all(
        s.reason == ArchiveSkipReason.invalid_required_field for s in result.skipped
    )


def test_archive_papers_dedupes_duplicate_input_identity(session: Session) -> None:
    first = _candidate(source_uid="100", doi="10.1000/a", title="First")
    second = _candidate(source_uid="100", doi="10.1000/a", title="Second")
    other = _candidate(source_uid="200", doi="10.1000/b", title="Other")

    result = archive_papers(session, [first, second, other])

    assert [p.source_uid for p in result.papers] == ["100", "200"]
    assert result.papers[0].title == "First"
    assert result.skipped == []
    assert result.errors == []


def test_archive_papers_records_duplicate_skip_once(session: Session) -> None:
    result = archive_papers(
        session,
        [
            _candidate(doi=None, source_uid="1"),
            _candidate(doi=None, source_uid="1"),
        ],
    )

    assert result.papers == []
    assert len(result.skipped) == 1
    assert result.skipped[0].reason == ArchiveSkipReason.missing_doi


def test_archive_papers_savepoint_failure_records_error_and_continues(
    session: Session,
) -> None:
    good = _candidate(source_uid="100", doi="10.1000/good")
    bad = _candidate(source_uid="200", doi="10.1000/bad")
    after = _candidate(source_uid="300", doi="10.1000/after")

    from paper_reviewer.models.paper import Paper as OrmPaper

    original_flush = session.flush

    def flush_with_failure(*args: object, **kwargs: object) -> None:
        for obj in session.new:
            if isinstance(obj, OrmPaper) and obj.source_uid == "200":
                raise RuntimeError("simulated flush failure")
        return original_flush(*args, **kwargs)

    with patch.object(session, "flush", side_effect=flush_with_failure):
        result = archive_papers(session, [good, bad, after])

    assert [p.source_uid for p in result.papers] == ["100", "300"]
    assert len(result.errors) == 1
    assert result.errors[0].source_uid == "200"
    assert "simulated flush failure" in result.errors[0].reason
    assert get_paper_by_source_handle(session, "pubmed", "200") is None
