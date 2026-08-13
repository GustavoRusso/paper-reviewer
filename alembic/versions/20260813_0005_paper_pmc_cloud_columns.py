"""Add Paper PMC Cloud enrichment columns.

Revision ID: 20260813_0005
Revises: 20260812_0004
Create Date: 2026-08-13
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260813_0005"
down_revision: str | None = "20260812_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("papers", sa.Column("pmcid", sa.Text(), nullable=True))
    op.add_column("papers", sa.Column("pmcid_version", sa.Integer(), nullable=True))
    op.add_column("papers", sa.Column("is_open_access", sa.Boolean(), nullable=True))
    op.add_column("papers", sa.Column("full_text_plain", sa.Text(), nullable=True))
    op.add_column(
        "papers",
        sa.Column("open_access_pdf_url", sa.Text(), nullable=True),
    )
    op.add_column("papers", sa.Column("pmc_article_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("papers", "pmc_article_url")
    op.drop_column("papers", "open_access_pdf_url")
    op.drop_column("papers", "full_text_plain")
    op.drop_column("papers", "is_open_access")
    op.drop_column("papers", "pmcid_version")
    op.drop_column("papers", "pmcid")
