"""Topic brief generation ORM model and persistence helpers."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, Text, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column
from sqlalchemy.types import Uuid

from paper_reviewer.models.base import Base
from paper_reviewer.schemas.topic_intake import TopicStatement, accept_topic_intake


class TopicBriefGeneration(Base):
    """One end-to-end Topic brief generation run (intake through topic brief)."""

    __tablename__ = "topic_brief_generations"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    public_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid.uuid4,
    )
    topic_statement: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


def create_topic_brief_generation(
    session: Session,
    topic_statement: str,
) -> TopicBriefGeneration:
    """Persist a new Topic brief generation for ``topic_statement``."""
    generation = TopicBriefGeneration(topic_statement=topic_statement)
    session.add(generation)
    return generation


def get_topic_brief_generation_by_public_id(
    session: Session,
    public_id: uuid.UUID,
) -> TopicBriefGeneration | None:
    """Return the generation with ``public_id``, or ``None`` if missing."""
    return session.scalar(
        select(TopicBriefGeneration).where(
            TopicBriefGeneration.public_id == public_id
        )
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
