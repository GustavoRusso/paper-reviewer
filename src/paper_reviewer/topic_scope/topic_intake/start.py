"""Start a Topic scope from Topic intake text."""

from __future__ import annotations

from sqlalchemy.orm import Session

from paper_reviewer.models.topic_brief_generation import (
    TopicScope,
    create_topic_scope,
)
from paper_reviewer.schemas.topic_brief_generation.topic_intake import (
    TopicStatement,
    accept_topic_intake,
)


def start_topic_scope_from_topic_intake(
    session: Session,
    raw_text: str,
) -> tuple[TopicStatement, TopicScope]:
    """Validate Topic intake text and persist a Topic scope."""
    topic_statement = accept_topic_intake(raw_text)
    topic_scope = create_topic_scope(session, topic_statement.text)
    session.flush()
    return topic_statement, topic_scope
