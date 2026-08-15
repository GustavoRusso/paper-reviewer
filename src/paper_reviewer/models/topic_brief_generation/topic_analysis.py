"""Topic facet ORM mappings and thin list/delete helpers."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Text,
    UniqueConstraint,
    delete,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column

from paper_reviewer.models.base import Base


class TopicFacet(Base):
    """One persisted topic facet row for a Topic scope."""

    __tablename__ = "topic_facets"
    __table_args__ = (
        UniqueConstraint(
            "topic_scope_id",
            "facet_id",
            name="uq_topic_facets_topic_scope_id_facet_id",
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
    topic_scope_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("topic_scopes.id"),
        nullable=False,
    )
    facet_id: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    concepts: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=False,
    )
    synonyms: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=False,
    )
    date_from: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_to: Mapped[str | None] = mapped_column(Text, nullable=True)
    filters: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=False,
    )
    retmax: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)


def list_topic_facets_for_scope(
    session: Session,
    topic_scope_id: int,
) -> Sequence[TopicFacet]:
    """Return facet rows for a Topic scope, ordered by position."""
    return session.scalars(
        select(TopicFacet)
        .where(TopicFacet.topic_scope_id == topic_scope_id)
        .order_by(TopicFacet.position)
    ).all()


def delete_topic_facets_for_scope(session: Session, topic_scope_id: int) -> None:
    """Delete all facet rows for a Topic scope."""
    session.execute(
        delete(TopicFacet).where(TopicFacet.topic_scope_id == topic_scope_id)
    )
