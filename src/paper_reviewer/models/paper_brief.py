"""PaperBrief ORM mapping and thin persistence helpers."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Text,
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


class PaperBrief(Base):
    """Global topic-agnostic brief for one Paper (1:1)."""

    __tablename__ = "paper_briefs"

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
    paper_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("papers.id"),
        unique=True,
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
    paper: Mapped["Paper"] = relationship(  # noqa: F821
        "Paper",
        back_populates="paper_brief",
    )


def create_paper_brief_row(
    session: Session,
    *,
    paper_id: int,
    status: PaperAspectStatus = PaperAspectStatus.not_started,
    error_message: str | None = None,
) -> PaperBrief:
    """Add a new PaperBrief row to the session (caller flushes/commits)."""
    brief = PaperBrief(
        paper_id=paper_id,
        status=status,
        error_message=error_message,
    )
    session.add(brief)
    return brief


def get_paper_brief_by_paper_id(session: Session, paper_id: int) -> PaperBrief | None:
    """Return the PaperBrief for ``paper_id``, or ``None``."""
    return session.scalar(select(PaperBrief).where(PaperBrief.paper_id == paper_id))
