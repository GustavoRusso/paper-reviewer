"""TopicBriefGeneration aggregate root and thin persistence helpers."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, Text, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column
from sqlalchemy.types import Uuid

from paper_reviewer.models.base import Base


class TopicBriefGeneration(Base):
    """One end-to-end Topic brief generation run (intake through topic brief)."""

    __tablename__ = "topic_brief_generations"
    __table_args__ = (
        UniqueConstraint("key", name="uq_topic_brief_generations_key"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    key: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
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


def get_topic_brief_generation_by_key(
    session: Session,
    key: uuid.UUID,
) -> TopicBriefGeneration | None:
    """Return the generation with ``key``, or ``None`` if missing."""
    return session.scalar(
        select(TopicBriefGeneration).where(TopicBriefGeneration.key == key)
    )


def list_topic_brief_generations(
    session: Session,
) -> Sequence[TopicBriefGeneration]:
    """Return all Topic brief generations, newest ``created_at`` first."""
    return session.scalars(
        select(TopicBriefGeneration).order_by(
            TopicBriefGeneration.created_at.desc()
        )
    ).all()
