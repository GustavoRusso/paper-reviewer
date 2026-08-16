"""Papers search: match topic facet concepts against Paper.keywords_tsv."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from paper_reviewer.models.paper import Paper
from paper_reviewer.models.topic_brief_generation import TopicScope
from paper_reviewer.models.topic_brief_generation.reference import Reference
from paper_reviewer.models.topic_brief_generation.topic_analysis import (
    list_topic_facets_for_scope,
)
from paper_reviewer.schemas.topic_brief_generation.papers_search import (
    PaperSearchHit,
    PapersSearchResult,
)

HIT_LIMIT = 20
_FETCH_LIMIT = HIT_LIMIT + 1


def keywords_match_any(concepts: Sequence[str]) -> ColumnElement[bool]:
    """Return ``Paper.keywords_tsv @@ (q1 || q2 || …)`` for ``simple`` config."""
    queries = [
        func.plainto_tsquery("simple", concept) for concept in concepts
    ]
    combined = queries[0]
    for query in queries[1:]:
        combined = combined.op("||")(query)
    return Paper.keywords_tsv.op("@@")(combined)


def _usable_concepts(session: Session, topic_scope: TopicScope) -> list[str]:
    seen: set[str] = set()
    concepts: list[str] = []
    for facet in list_topic_facets_for_scope(session, topic_scope.id):
        for raw in facet.concepts:
            concept = raw.strip()
            if not concept or concept in seen:
                continue
            seen.add(concept)
            concepts.append(concept)
    return concepts


def _referenced_paper_ids(
    session: Session,
    topic_scope_id: int,
) -> set[int]:
    rows = session.scalars(
        select(Reference.paper_id).where(
            Reference.topic_scope_id == topic_scope_id
        )
    ).all()
    return set(rows)


def _to_hit(paper: Paper, *, already_referenced: bool) -> PaperSearchHit:
    return PaperSearchHit(
        title=paper.title,
        url=paper.url,
        doi=paper.doi,
        authors=list(paper.authors),
        journal=paper.journal,
        published_year=paper.published_year,
        already_referenced=already_referenced,
    )


def search_papers(
    session: Session,
    topic_scope: TopicScope,
) -> PapersSearchResult:
    """Return Papers that match any facet concept for ``topic_scope``."""
    concepts = _usable_concepts(session, topic_scope)
    if not concepts:
        return PapersSearchResult(hits=[], truncated=False)

    papers = list(
        session.scalars(
            select(Paper)
            .where(keywords_match_any(concepts))
            .order_by(Paper.id)
            .limit(_FETCH_LIMIT)
        ).all()
    )
    truncated = len(papers) > HIT_LIMIT
    papers = papers[:HIT_LIMIT]
    referenced_ids = _referenced_paper_ids(session, topic_scope.id)
    return PapersSearchResult(
        hits=[
            _to_hit(paper, already_referenced=paper.id in referenced_ids)
            for paper in papers
        ],
        truncated=truncated,
    )
