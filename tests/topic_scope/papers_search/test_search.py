"""search_papers: concepts → FTS match → hits with already_referenced."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest
from sqlalchemy import ColumnElement, create_engine, select, true
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.paper import Paper, create_paper
from paper_reviewer.models.paper_brief import create_paper_brief_row
from paper_reviewer.models.topic_scope import (
    TopicFacet,
    TopicScope,
    create_topic_scope,
)
from paper_reviewer.models.topic_scope.reference import create_reference
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.papers_search import (
    PapersSearchResult,
)
from paper_reviewer.topic_scope.papers_search import (
    keywords_match_any,
    search_papers,
)


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


def _add_facet(
    session: Session,
    topic_scope: TopicScope,
    *,
    concepts: list[str],
    facet_id: str = "core-concepts",
    position: int = 0,
) -> TopicFacet:
    row = TopicFacet(
        topic_scope_id=topic_scope.id,
        facet_id=facet_id,
        label="Core concepts",
        intent=None,
        concepts=concepts,
        synonyms=[],
        filters={},
        position=position,
    )
    session.add(row)
    session.flush()
    return row


def _add_paper(
    session: Session,
    *,
    doi: str,
    source_uid: str,
    title: str,
    authors: list[str] | None = None,
    journal: str | None = "Nature",
    published_year: int | None = 2024,
) -> Paper:
    paper = create_paper(
        session,
        doi=doi,
        source_id="pubmed",
        source_uid=source_uid,
        title=title,
        authors=authors if authors is not None else ["Ada Lovelace"],
        url=f"https://example.com/{source_uid}",
        journal=journal,
        published_year=published_year,
    )
    session.flush()
    return paper


def test_keywords_match_any_compiles_plainto_tsquery_or_and_match() -> None:
    clause = keywords_match_any(["glioblastoma", "immunotherapy"])
    compiled = (
        select(Paper)
        .where(clause)
        .compile(dialect=postgresql.dialect())
    )
    sql = str(compiled)

    assert "plainto_tsquery" in sql
    assert "@@" in sql
    assert "||" in sql
    assert "match(" not in sql.lower()
    assert "to_tsquery(" not in sql.replace("plainto_tsquery(", "")
    assert "simple" in compiled.params.values() or "simple" in sql


def test_search_papers_empty_when_no_usable_concepts(session: Session) -> None:
    topic_scope = create_topic_scope(session, "no concepts")
    session.flush()
    _add_facet(session, topic_scope, concepts=["  ", ""])
    _add_paper(
        session,
        doi="10.1000/SHOULD-NOT-MATCH",
        source_uid="1",
        title="Should not be scanned",
    )

    with patch(
        "paper_reviewer.topic_scope.papers_search.search.keywords_match_any",
    ) as match_mock:
        result = search_papers(session, topic_scope)

    assert isinstance(result, PapersSearchResult)
    assert result.hits == []
    match_mock.assert_not_called()


def test_search_papers_maps_hits_and_already_referenced(
    session: Session,
) -> None:
    topic_scope = create_topic_scope(session, "with concepts")
    session.flush()
    _add_facet(
        session,
        topic_scope,
        concepts=[" glioblastoma ", "", "immunotherapy", "glioblastoma"],
    )
    referenced = _add_paper(
        session,
        doi="10.1000/REF",
        source_uid="10",
        title="Referenced paper",
        authors=["Ada Lovelace", "Alan Turing"],
        journal="Nature",
        published_year=2024,
    )
    other = _add_paper(
        session,
        doi="10.1000/NEW",
        source_uid="11",
        title="New paper",
        authors=[],
        journal=None,
        published_year=None,
    )
    create_reference(session, topic_scope.id, referenced.id)
    session.flush()

    def _match_all(_concepts: list[str]) -> ColumnElement[bool]:
        return true()

    with patch(
        "paper_reviewer.topic_scope.papers_search.search.keywords_match_any",
        side_effect=_match_all,
    ) as match_mock:
        result = search_papers(session, topic_scope)

    match_mock.assert_called_once_with(["glioblastoma", "immunotherapy"])
    assert [hit.doi for hit in result.hits] == ["10.1000/REF", "10.1000/NEW"]
    first, second = result.hits
    assert first.title == "Referenced paper"
    assert first.url == "https://example.com/10"
    assert first.authors == ["Ada Lovelace", "Alan Turing"]
    assert first.journal == "Nature"
    assert first.published_year == 2024
    assert first.already_referenced is True
    assert first.paper_brief_available is False
    assert second.title == "New paper"
    assert second.authors == []
    assert second.journal is None
    assert second.published_year is None
    assert second.already_referenced is False
    assert second.paper_brief_available is False
    assert other.id is not None


def test_search_papers_maps_paper_brief_available_when_succeeded(
    session: Session,
) -> None:
    topic_scope = create_topic_scope(session, "brief ready")
    session.flush()
    _add_facet(session, topic_scope, concepts=["keyword"])
    with_brief = _add_paper(
        session, doi="10.1000/BRIEF", source_uid="20", title="With brief"
    )
    without = _add_paper(
        session, doi="10.1000/NONE", source_uid="21", title="No brief"
    )
    create_paper_brief_row(
        session, paper_id=with_brief.id, status=PaperAspectStatus.succeeded
    )
    create_paper_brief_row(
        session, paper_id=without.id, status=PaperAspectStatus.failed
    )
    session.flush()

    with patch(
        "paper_reviewer.topic_scope.papers_search.search.keywords_match_any",
        return_value=true(),
    ):
        result = search_papers(session, topic_scope)

    by_doi = {hit.doi: hit for hit in result.hits}
    assert by_doi["10.1000/BRIEF"].paper_brief_available is True
    assert by_doi["10.1000/NONE"].paper_brief_available is False


def test_search_papers_returns_all_matching_papers(session: Session) -> None:
    topic_scope = create_topic_scope(session, "many papers")
    session.flush()
    _add_facet(session, topic_scope, concepts=["keyword"])
    match_count = 21
    for index in range(match_count):
        _add_paper(
            session,
            doi=f"10.1000/{index}",
            source_uid=str(index),
            title=f"Paper {index}",
        )

    with patch(
        "paper_reviewer.topic_scope.papers_search.search.keywords_match_any",
        return_value=true(),
    ):
        result = search_papers(session, topic_scope)

    assert len(result.hits) == match_count
    assert [hit.doi for hit in result.hits] == [
        f"10.1000/{index}" for index in range(match_count)
    ]
    assert "truncated" not in PapersSearchResult.model_fields
