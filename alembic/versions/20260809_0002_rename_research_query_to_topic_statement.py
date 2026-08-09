"""Rename research_query to topic_statement.

Revision ID: 20260809_0002
Revises: 20260807_0001
Create Date: 2026-08-09
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260809_0002"
down_revision: str | None = "20260807_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "topic_brief_generations",
        "research_query",
        new_column_name="topic_statement",
    )


def downgrade() -> None:
    op.alter_column(
        "topic_brief_generations",
        "topic_statement",
        new_column_name="research_query",
    )
