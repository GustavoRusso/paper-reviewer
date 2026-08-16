"""run_topic_analysis: persist, reload, replace."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.topic_scope import (
    TopicFacet,
    create_topic_scope,
)
from paper_reviewer.schemas.topic_scope.topic_analysis import (
    TopicAnalysisResult,
)
from paper_reviewer.topic_scope.topic_analysis import (
    load_topic_analysis_result,
    run_topic_analysis,
)


@dataclass
class FakeSpan:
    text: str


@dataclass
class FakeDoc:
    ents: list[FakeSpan] = field(default_factory=list)
    tokens: list[object] = field(default_factory=list)

    def __iter__(self):
        return iter(self.tokens)


class FakeNlp:
    def __init__(self, doc: FakeDoc) -> None:
        self._doc = doc

    def __call__(self, text: str) -> FakeDoc:
        return self._doc


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


def test_run_topic_analysis_persists_and_reloads(session: Session) -> None:
    topic_scope = create_topic_scope(session, "glioblastoma immunotherapy")
    session.flush()
    nlp = FakeNlp(
        FakeDoc(ents=[FakeSpan("glioblastoma"), FakeSpan("immunotherapy")])
    )

    result = run_topic_analysis(session, topic_scope, nlp=nlp)

    assert isinstance(result, TopicAnalysisResult)
    assert len(result.facets) == 1
    facet = result.facets[0]
    assert facet.id == "core-concepts"
    assert facet.label == "Core concepts"
    assert facet.intent == "Narrow topical match from biomedical entities"
    assert facet.concepts == ["glioblastoma", "immunotherapy"]
    assert facet.synonyms == []
    assert facet.filters == {}
    assert facet.date_from is None
    assert facet.date_to is None
    assert facet.retmax is None

    reloaded = load_topic_analysis_result(session, topic_scope)
    assert reloaded.model_dump() == result.model_dump()
    row_count = session.scalar(select(func.count()).select_from(TopicFacet))
    assert row_count == 1


def test_run_topic_analysis_replaces_existing_rows(session: Session) -> None:
    topic_scope = create_topic_scope(session, "glioblastoma")
    session.flush()
    run_topic_analysis(
        session,
        topic_scope,
        nlp=FakeNlp(FakeDoc(ents=[FakeSpan("old-term")])),
    )

    result = run_topic_analysis(
        session,
        topic_scope,
        nlp=FakeNlp(FakeDoc(ents=[FakeSpan("glioblastoma")])),
    )

    assert result.facets[0].concepts == ["glioblastoma"]
    row_count = session.scalar(select(func.count()).select_from(TopicFacet))
    assert row_count == 1
    reloaded = load_topic_analysis_result(session, topic_scope)
    assert reloaded.facets[0].concepts == ["glioblastoma"]


def test_run_topic_analysis_empty_text_raises_and_writes_no_rows(
    session: Session,
) -> None:
    topic_scope = create_topic_scope(session, "   ")
    session.flush()

    with pytest.raises(ValueError):
        run_topic_analysis(session, topic_scope, nlp=FakeNlp(FakeDoc()))

    row_count = session.scalar(select(func.count()).select_from(TopicFacet))
    assert row_count == 0


def test_load_topic_analysis_result_empty_when_no_rows(session: Session) -> None:
    topic_scope = create_topic_scope(session, "no facets yet")
    session.flush()

    result = load_topic_analysis_result(session, topic_scope)

    assert result == TopicAnalysisResult(facets=[])
