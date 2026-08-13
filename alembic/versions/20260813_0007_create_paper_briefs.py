"""Create paper_briefs table (1:1 with papers).

Revision ID: 20260813_0007
Revises: 20260813_0006
Create Date: 2026-08-13
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260813_0007"
down_revision: str | None = "20260813_0006"
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
        "paper_briefs",
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
        sa.Column("paper_id", sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("paper_id"),
    )


def downgrade() -> None:
    op.drop_table("paper_briefs")
