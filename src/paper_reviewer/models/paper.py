"""Paper ORM mapping and thin persistence helpers."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
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
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    PaperAspectStatus,
)

_ASPECT_STATUS = Enum(
    PaperAspectStatus,
    name="paper_aspect_status",
    native_enum=False,
    length=32,
    values_callable=lambda cls: [member.value for member in cls],
)


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
    source_record: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True,
    )
    source_record_status: Mapped[PaperAspectStatus] = mapped_column(
        _ASPECT_STATUS,
        nullable=False,
        default=PaperAspectStatus.not_started,
        server_default="not_started",
    )
    source_record_error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    full_text_status: Mapped[PaperAspectStatus] = mapped_column(
        _ASPECT_STATUS,
        nullable=False,
        default=PaperAspectStatus.not_started,
        server_default="not_started",
    )
    full_text_error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    pub_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    abstract_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    pmcid: Mapped[str | None] = mapped_column(Text, nullable=True)
    pmcid_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_open_access: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    full_text_plain: Mapped[str | None] = mapped_column(Text, nullable=True)
    open_access_pdf_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    pmc_article_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    paper_brief: Mapped["PaperBrief | None"] = relationship(  # noqa: F821
        "PaperBrief",
        back_populates="paper",
        uselist=False,
    )


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


def get_paper_by_id(session: Session, paper_id: int) -> Paper | None:
    """Return the Paper with primary key ``paper_id``, or ``None``."""
    return session.get(Paper, paper_id)


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
