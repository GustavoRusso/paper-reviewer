"""Add last-run OpenAI usage integers to paper_briefs.

Revision ID: 20260817_0014
Revises: 20260816_0013
Create Date: 2026-08-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260817_0014"
down_revision: str | None = "20260816_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "paper_briefs",
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "paper_briefs",
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "paper_briefs",
        sa.Column("total_tokens", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("paper_briefs", "total_tokens")
    op.drop_column("paper_briefs", "completion_tokens")
    op.drop_column("paper_briefs", "prompt_tokens")
