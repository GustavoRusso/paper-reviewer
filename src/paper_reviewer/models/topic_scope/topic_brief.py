"""TopicBrief ORM mapping and thin persistence helpers."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Text,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from paper_reviewer.models.base import Base
from paper_reviewer.models.paper import _ASPECT_STATUS
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)


class TopicBrief(Base):
    """Topic-conditioned brief for one Topic scope (1:1)."""

    __tablename__ = "topic_briefs"
    __table_args__ = (
        UniqueConstraint(
            "topic_scope_id",
            name="uq_topic_briefs_topic_scope_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    topic_scope_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("topic_scopes.id"),
        nullable=False,
    )
    status: Mapped[PaperAspectStatus] = mapped_column(
        _ASPECT_STATUS,
        nullable=False,
        default=PaperAspectStatus.not_started,
        server_default="not_started",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True,
    )
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    topic_scope: Mapped["TopicScope"] = relationship(  # noqa: F821
        "TopicScope",
        back_populates="topic_brief",
    )


def create_topic_brief_row(
    session: Session,
    *,
    topic_scope_id: int,
    status: PaperAspectStatus = PaperAspectStatus.not_started,
    error_message: str | None = None,
) -> TopicBrief:
    """Add a new TopicBrief row to the session (caller flushes/commits)."""
    brief = TopicBrief(
        topic_scope_id=topic_scope_id,
        status=status,
        error_message=error_message,
    )
    session.add(brief)
    return brief


def get_topic_brief_by_topic_scope_id(
    session: Session,
    topic_scope_id: int,
) -> TopicBrief | None:
    """Return the TopicBrief for ``topic_scope_id``, or ``None``."""
    return session.scalar(
        select(TopicBrief).where(TopicBrief.topic_scope_id == topic_scope_id)
    )
