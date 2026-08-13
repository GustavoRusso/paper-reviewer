"""Replace source-inform timestamp with per-aspect Paper statuses.

Revision ID: 20260813_0006
Revises: 20260813_0005
Create Date: 2026-08-13
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260813_0006"
down_revision: str | None = "20260813_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ASPECT_VALUES = ("not_started", "succeeded", "failed", "unavailable")


def _aspect_status(*, create_type: bool) -> postgresql.ENUM:
    return postgresql.ENUM(
        *_ASPECT_VALUES,
        name="paper_aspect_status",
        create_type=create_type,
    )


def upgrade() -> None:
    bind = op.get_bind()
    _aspect_status(create_type=True).create(bind, checkfirst=True)
    status_type = _aspect_status(create_type=False)
    op.add_column(
        "papers",
        sa.Column(
            "source_record_status",
            status_type,
            nullable=False,
            server_default="not_started",
        ),
    )
    op.add_column(
        "papers",
        sa.Column("source_record_error_message", sa.Text(), nullable=True),
    )
    op.add_column(
        "papers",
        sa.Column(
            "full_text_status",
            status_type,
            nullable=False,
            server_default="not_started",
        ),
    )
    op.add_column(
        "papers",
        sa.Column("full_text_error_message", sa.Text(), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE papers SET
              source_record_status = CASE
                WHEN source_informed_at IS NOT NULL
                  THEN 'succeeded'::paper_aspect_status
                WHEN source_inform_error_message IS NOT NULL
                  THEN 'failed'::paper_aspect_status
                ELSE 'not_started'::paper_aspect_status
              END,
              full_text_status = CASE
                WHEN source_informed_at IS NOT NULL
                  AND full_text_plain IS NOT NULL
                  THEN 'succeeded'::paper_aspect_status
                WHEN source_informed_at IS NOT NULL
                  AND full_text_plain IS NULL
                  THEN 'unavailable'::paper_aspect_status
                ELSE 'not_started'::paper_aspect_status
              END,
              source_record_error_message = CASE
                WHEN source_informed_at IS NULL
                  THEN source_inform_error_message
                ELSE NULL
              END
            """
        )
    )
    op.drop_column("papers", "source_inform_error_message")
    op.drop_column("papers", "source_informed_at")


def downgrade() -> None:
    op.add_column(
        "papers",
        sa.Column("source_informed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "papers",
        sa.Column("source_inform_error_message", sa.Text(), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE papers SET
              source_informed_at = CASE
                WHEN source_record_status = 'succeeded'::paper_aspect_status
                  THEN CURRENT_TIMESTAMP
                ELSE NULL
              END,
              source_inform_error_message = source_record_error_message
            """
        )
    )
    op.drop_column("papers", "full_text_error_message")
    op.drop_column("papers", "full_text_status")
    op.drop_column("papers", "source_record_error_message")
    op.drop_column("papers", "source_record_status")
    _aspect_status(create_type=False).drop(op.get_bind(), checkfirst=True)
