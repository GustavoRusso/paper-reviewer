"""Attach ingested Papers as References for a Topic scope."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from paper_reviewer.models.paper import get_paper_by_doi
from paper_reviewer.models.topic_brief_generation import TopicScope
from paper_reviewer.models.topic_brief_generation.reference import (
    Reference,
    create_reference,
)


class AddReferenceError(Exception):
    """Raised when a DOI cannot be attached as a Reference."""


def _referenced_paper_ids(session: Session, topic_scope_id: int) -> set[int]:
    rows = session.scalars(
        select(Reference.paper_id).where(
            Reference.topic_scope_id == topic_scope_id
        )
    ).all()
    return set(rows)


def add_references(
    session: Session,
    topic_scope: TopicScope,
    dois: Sequence[str],
) -> None:
    """Attach Papers identified by ``dois`` as References on ``topic_scope``."""
    referenced_ids = _referenced_paper_ids(session, topic_scope.id)
    for raw in dois:
        doi = raw.strip().upper()
        if not doi:
            raise AddReferenceError("DOI is blank.")
        paper = get_paper_by_doi(session, doi)
        if paper is None:
            raise AddReferenceError(f"No Paper for DOI {doi}.")
        if paper.id in referenced_ids:
            continue
        create_reference(session, topic_scope.id, paper.id)
        referenced_ids.add(paper.id)
