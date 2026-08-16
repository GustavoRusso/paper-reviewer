"""Create topic_briefs table (1:1 with topic_scopes).

Revision ID: 20260816_0013
Revises: 20260816_0012
Create Date: 2026-08-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260816_0013"
down_revision: str | None = "20260816_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    status_type = postgresql.ENUM(
        "not_started",
        "succeeded",
        "failed",
        "unavailable",
        name="paper_aspect_status",
        create_type=False,
    )
    op.create_table(
        "topic_briefs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("topic_scope_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            status_type,
            server_default="not_started",
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "content",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["topic_scope_id"], ["topic_scopes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "topic_scope_id",
            name="uq_topic_briefs_topic_scope_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("topic_briefs")
