"""Create topic_facets table.

Revision ID: 20260815_0010
Revises: 20260815_0009
Create Date: 2026-08-15
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260815_0010"
down_revision: str | None = "20260815_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "topic_facets",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("topic_scope_id", sa.BigInteger(), nullable=False),
        sa.Column("facet_id", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("intent", sa.Text(), nullable=True),
        sa.Column(
            "concepts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "synonyms",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("date_from", sa.Text(), nullable=True),
        sa.Column("date_to", sa.Text(), nullable=True),
        sa.Column(
            "filters",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("retmax", sa.Integer(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["topic_scope_id"], ["topic_scopes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "topic_scope_id",
            "facet_id",
            name="uq_topic_facets_topic_scope_id_facet_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("topic_facets")
