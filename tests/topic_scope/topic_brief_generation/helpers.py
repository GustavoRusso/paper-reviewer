"""Shared helpers for topic brief generation domain tests."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.paper import create_paper
from paper_reviewer.models.paper_brief import create_paper_brief_row
from paper_reviewer.models.topic_scope import create_topic_scope
from paper_reviewer.models.topic_scope.reference import create_reference
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.topic_brief_generation import (
    TopicBriefContent,
)


def sample_topic_brief_content(**overrides: object) -> TopicBriefContent:
    data: dict[str, object] = {
        "title": "Example topic brief title for indexing",
        "abstract": "A short abstract without citations.",
        "introduction": "Background and why it matters.[1]",
        "sections": [{"heading": "Main theme", "body": "Discussion of evidence.[1]"}],
        "concluding_section": "Summary of the viewpoint.",
        "key_points": ["Key point one"],
        "citations": [
            {
                "n": 1,
                "doi": "10.1000/EXAMPLE",
                "text": "10.1000/EXAMPLE — Example title",
            }
        ],
    }
    data.update(overrides)
    return TopicBriefContent.model_validate(data)


def create_test_scope(
    factory: sessionmaker[Session],
    *,
    statement: str = "glioblastoma immunotherapy",
) -> int:
    session = factory()
    try:
        topic_scope = create_topic_scope(session, statement)
        session.commit()
        return topic_scope.id
    finally:
        session.close()


def add_briefed_reference(
    factory: sessionmaker[Session],
    topic_scope_id: int,
    *,
    uid: str = "100",
    doi: str = "10.1000/EXAMPLE",
) -> int:
    session = factory()
    try:
        paper = create_paper(
            session,
            doi=doi,
            source_id="pubmed",
            source_uid=uid,
            title="Example title",
            authors=["Ada Lovelace"],
            url=f"https://example.com/{uid}",
            journal="Nature",
            published_year=2024,
        )
        session.flush()
        create_reference(session, topic_scope_id, paper.id)
        create_paper_brief_row(
            session,
            paper_id=paper.id,
            status=PaperAspectStatus.succeeded,
        )
        session.commit()
        return paper.id
    finally:
        session.close()
