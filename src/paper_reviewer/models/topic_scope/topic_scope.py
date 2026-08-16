"""TopicScope aggregate root and thin persistence helpers."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, Text, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship
from sqlalchemy.types import Uuid

from paper_reviewer.models.base import Base


class TopicScope(Base):
    """Durable record of one topic (intake through topic brief)."""

    __tablename__ = "topic_scopes"
    __table_args__ = (
        UniqueConstraint("key", name="uq_topic_scopes_key"),
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
    topic_brief: Mapped["TopicBrief | None"] = relationship(  # noqa: F821
        "TopicBrief",
        back_populates="topic_scope",
        uselist=False,
    )


def create_topic_scope(
    session: Session,
    topic_statement: str,
) -> TopicScope:
    """Persist a new Topic scope for ``topic_statement``."""
    topic_scope = TopicScope(topic_statement=topic_statement)
    session.add(topic_scope)
    return topic_scope


def get_topic_scope_by_key(
    session: Session,
    key: uuid.UUID,
) -> TopicScope | None:
    """Return the Topic scope with ``key``, or ``None`` if missing."""
    return session.scalar(
        select(TopicScope).where(TopicScope.key == key)
    )


def list_topic_scopes(
    session: Session,
) -> Sequence[TopicScope]:
    """Return all Topic scopes, newest ``created_at`` first."""
    return session.scalars(
        select(TopicScope).order_by(
            TopicScope.created_at.desc()
        )
    ).all()
