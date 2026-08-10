"""Start a Topic brief generation from Topic intake text."""

from __future__ import annotations

from sqlalchemy.orm import Session

from paper_reviewer.models.topic_brief_generation import (
    TopicBriefGeneration,
    create_topic_brief_generation,
)
from paper_reviewer.schemas.topic_brief_generation.topic_intake import (
    TopicStatement,
    accept_topic_intake,
)


def start_topic_brief_from_topic_intake(
    session: Session,
    raw_text: str,
) -> tuple[TopicStatement, TopicBriefGeneration]:
    """Validate Topic intake text and persist a Topic brief generation."""
    topic_statement = accept_topic_intake(raw_text)
    generation = create_topic_brief_generation(session, topic_statement.text)
    session.flush()
    return topic_statement, generation
