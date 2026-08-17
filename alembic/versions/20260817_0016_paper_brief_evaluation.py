"""Add G-Eval evaluation columns to paper_briefs.

Revision ID: 20260817_0016
Revises: 20260817_0015
Create Date: 2026-08-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260817_0016"
down_revision: str | None = "20260817_0015"
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
    op.add_column(
        "paper_briefs",
        sa.Column(
            "evaluation_status",
            status_type,
            server_default="not_started",
            nullable=False,
        ),
    )
    op.add_column(
        "paper_briefs",
        sa.Column(
            "evaluation",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "paper_briefs",
        sa.Column("evaluation_score", sa.Numeric(3, 2), nullable=True),
    )
    op.add_column(
        "paper_briefs",
        sa.Column("evaluation_error_message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("paper_briefs", "evaluation_error_message")
    op.drop_column("paper_briefs", "evaluation_score")
    op.drop_column("paper_briefs", "evaluation")
    op.drop_column("paper_briefs", "evaluation_status")
