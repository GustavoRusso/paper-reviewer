"""Paper ORM mapping and thin persistence helpers."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Integer,
    JSON,
    Text,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column

from paper_reviewer.models.base import Base


class Paper(Base):
    """Durable bibliographic record of a scientific article."""

    __tablename__ = "papers"
    __table_args__ = (
        UniqueConstraint("source_id", "source_uid", name="uq_papers_source_handle"),
        UniqueConstraint("doi", name="uq_papers_doi"),
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
    doi: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    source_uid: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=False,
    )
    journal: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)


def create_paper(
    session: Session,
    *,
    doi: str,
    source_id: str,
    source_uid: str,
    title: str,
    authors: list[str],
    url: str,
    journal: str | None = None,
    published_year: int | None = None,
) -> Paper:
    """Add a new Paper row to the session (caller flushes/commits)."""
    paper = Paper(
        doi=doi,
        source_id=source_id,
        source_uid=source_uid,
        title=title,
        authors=authors,
        journal=journal,
        published_year=published_year,
        url=url,
    )
    session.add(paper)
    return paper


def get_paper_by_source_handle(
    session: Session,
    source_id: str,
    source_uid: str,
) -> Paper | None:
    """Return the Paper with ``(source_id, source_uid)``, or ``None``."""
    return session.scalar(
        select(Paper).where(
            Paper.source_id == source_id,
            Paper.source_uid == source_uid,
        )
    )


def get_paper_by_doi(session: Session, doi: str) -> Paper | None:
    """Return the Paper with uppercase ``doi``, or ``None``.

    Callers must pass an already-normalized (uppercase) DOI.
    """
    return session.scalar(select(Paper).where(Paper.doi == doi))
