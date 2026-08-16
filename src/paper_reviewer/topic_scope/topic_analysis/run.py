"""Analyze a Topic scope and persist its topic facets."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from paper_reviewer.models.topic_scope import TopicScope
from paper_reviewer.models.topic_scope.topic_analysis import (
    TopicFacet as TopicFacetRow,
    delete_topic_facets_for_scope,
    list_topic_facets_for_scope,
)
from paper_reviewer.schemas.topic_scope.topic_analysis import (
    TopicAnalysisResult,
    TopicFacet,
)
from paper_reviewer.topic_scope.topic_analysis.analyze import (
    analyze_topic_statement,
)


def _row_to_schema(row: TopicFacetRow) -> TopicFacet:
    return TopicFacet(
        id=row.facet_id,
        label=row.label,
        intent=row.intent,
        concepts=list(row.concepts),
        synonyms=list(row.synonyms),
        date_from=row.date_from,
        date_to=row.date_to,
        filters=dict(row.filters),
        retmax=row.retmax,
    )


def load_topic_analysis_result(
    session: Session,
    topic_scope: TopicScope,
) -> TopicAnalysisResult:
    """Reload persisted facet rows for ``topic_scope`` into a result."""
    rows = list_topic_facets_for_scope(session, topic_scope.id)
    return TopicAnalysisResult(facets=[_row_to_schema(row) for row in rows])


def run_topic_analysis(
    session: Session,
    topic_scope: TopicScope,
    *,
    nlp: Callable[[str], Any] | None = None,
) -> TopicAnalysisResult:
    """Analyze the scope statement, replace facet rows, and return the result."""
    result = analyze_topic_statement(topic_scope.topic_statement, nlp=nlp)
    delete_topic_facets_for_scope(session, topic_scope.id)
    for position, facet in enumerate(result.facets):
        session.add(
            TopicFacetRow(
                topic_scope_id=topic_scope.id,
                facet_id=facet.id,
                label=facet.label,
                intent=facet.intent,
                concepts=list(facet.concepts),
                synonyms=list(facet.synonyms),
                date_from=facet.date_from,
                date_to=facet.date_to,
                filters=dict(facet.filters),
                retmax=facet.retmax,
                position=position,
            )
        )
    session.flush()
    return load_topic_analysis_result(session, topic_scope)
