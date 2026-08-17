"""Add last-run OpenAI usage integers to topic_briefs.

Revision ID: 20260817_0015
Revises: 20260817_0014
Create Date: 2026-08-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260817_0015"
down_revision: str | None = "20260817_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "topic_briefs",
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "topic_briefs",
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "topic_briefs",
        sa.Column("total_tokens", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("topic_briefs", "total_tokens")
    op.drop_column("topic_briefs", "completion_tokens")
    op.drop_column("topic_briefs", "prompt_tokens")
