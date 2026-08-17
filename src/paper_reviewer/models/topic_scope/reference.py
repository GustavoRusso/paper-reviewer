"""Reference ORM mapping and thin create/list helpers."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, selectinload

from paper_reviewer.models.base import Base
from paper_reviewer.models.paper import Paper


class Reference(Base):
    """Many-to-many link from one Topic scope to one ingested Paper."""

    __tablename__ = "topic_references"
    __table_args__ = (
        UniqueConstraint(
            "topic_scope_id",
            "paper_id",
            name="uq_topic_references_topic_scope_id_paper_id",
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
    paper_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("papers.id"),
        nullable=False,
    )


def create_reference(
    session: Session,
    topic_scope_id: int,
    paper_id: int,
) -> Reference:
    """Add a Reference row to the session (caller flushes/commits)."""
    row = Reference(topic_scope_id=topic_scope_id, paper_id=paper_id)
    session.add(row)
    return row


def count_references_for_scope(
    session: Session,
    topic_scope_id: int,
) -> int:
    """Return how many References exist for a Topic scope."""
    count = session.scalar(
        select(func.count())
        .select_from(Reference)
        .where(Reference.topic_scope_id == topic_scope_id)
    )
    return int(count or 0)


def list_references_for_scope(
    session: Session,
    topic_scope_id: int,
) -> Sequence[tuple[Reference, Paper]]:
    """Return Reference+Paper pairs for a Topic scope, oldest first."""
    return session.execute(
        select(Reference, Paper)
        .join(Paper, Paper.id == Reference.paper_id)
        .options(selectinload(Paper.paper_brief))
        .where(Reference.topic_scope_id == topic_scope_id)
        .order_by(Reference.created_at, Reference.id)
    ).tuples().all()
