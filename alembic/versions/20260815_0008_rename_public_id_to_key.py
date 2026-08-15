"""Rename topic_brief_generations.public_id to key.

Revision ID: 20260815_0008
Revises: 20260813_0007
Create Date: 2026-08-15
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260815_0008"
down_revision: str | None = "20260813_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OLD_CONSTRAINT = "topic_brief_generations_public_id_key"
_NEW_CONSTRAINT = "uq_topic_brief_generations_key"


def upgrade() -> None:
    op.alter_column(
        "topic_brief_generations",
        "public_id",
        new_column_name="key",
        existing_type=sa.Uuid(),
        existing_nullable=False,
        existing_server_default=sa.text("gen_random_uuid()"),
    )
    op.execute(
        sa.text(
            f'ALTER TABLE topic_brief_generations '
            f'RENAME CONSTRAINT "{_OLD_CONSTRAINT}" TO "{_NEW_CONSTRAINT}"'
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            f'ALTER TABLE topic_brief_generations '
            f'RENAME CONSTRAINT "{_NEW_CONSTRAINT}" TO "{_OLD_CONSTRAINT}"'
        )
    )
    op.alter_column(
        "topic_brief_generations",
        "key",
        new_column_name="public_id",
        existing_type=sa.Uuid(),
        existing_nullable=False,
        existing_server_default=sa.text("gen_random_uuid()"),
    )
