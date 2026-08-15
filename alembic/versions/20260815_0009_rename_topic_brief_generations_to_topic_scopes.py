"""Rename topic_brief_generations to topic_scopes.

Revision ID: 20260815_0009
Revises: 20260815_0008
Create Date: 2026-08-15
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260815_0009"
down_revision: str | None = "20260815_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OLD_TABLE = "topic_brief_generations"
_NEW_TABLE = "topic_scopes"
_OLD_CONSTRAINT = "uq_topic_brief_generations_key"
_NEW_CONSTRAINT = "uq_topic_scopes_key"


def upgrade() -> None:
    op.rename_table(_OLD_TABLE, _NEW_TABLE)
    op.execute(
        sa.text(
            f'ALTER TABLE {_NEW_TABLE} '
            f'RENAME CONSTRAINT "{_OLD_CONSTRAINT}" TO "{_NEW_CONSTRAINT}"'
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            f'ALTER TABLE {_NEW_TABLE} '
            f'RENAME CONSTRAINT "{_NEW_CONSTRAINT}" TO "{_OLD_CONSTRAINT}"'
        )
    )
    op.rename_table(_NEW_TABLE, _OLD_TABLE)
