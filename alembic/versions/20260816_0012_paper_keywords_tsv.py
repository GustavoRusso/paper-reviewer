"""Add papers.keywords_tsv generated column and GIN index.

Revision ID: 20260816_0012
Revises: 20260816_0011
Create Date: 2026-08-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260816_0012"
down_revision: str | None = "20260816_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_KEYWORDS_TSV_GENERATOR = (
    "jsonb_to_tsvector('simple', coalesce(source_record->'indexing'->'keywords', '[]'::jsonb), '[\"string\"]')"
)


def upgrade() -> None:
    op.add_column(
        "papers",
        sa.Column(
            "keywords_tsv",
            postgresql.TSVECTOR(),
            sa.Computed(_KEYWORDS_TSV_GENERATOR, persisted=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_papers_keywords_tsv",
        "papers",
        ["keywords_tsv"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_papers_keywords_tsv", table_name="papers")
    op.drop_column("papers", "keywords_tsv")
