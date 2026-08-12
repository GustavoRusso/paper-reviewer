"""Add Paper source-inform columns for fulfill papers metadata.

Revision ID: 20260812_0004
Revises: 20260811_0003
Create Date: 2026-08-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260812_0004"
down_revision: str | None = "20260811_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "papers",
        sa.Column(
            "source_record",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "papers",
        sa.Column("source_informed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "papers",
        sa.Column("source_inform_error_message", sa.Text(), nullable=True),
    )
    op.add_column(
        "papers",
        sa.Column("pub_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "papers",
        sa.Column("abstract_text", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("papers", "abstract_text")
    op.drop_column("papers", "pub_date")
    op.drop_column("papers", "source_inform_error_message")
    op.drop_column("papers", "source_informed_at")
    op.drop_column("papers", "source_record")
