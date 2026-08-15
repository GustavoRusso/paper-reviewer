"""Landing page helpers: generation list formatting and empty copy."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from paper_reviewer.ui.landing import (
    EMPTY_GENERATIONS_MESSAGE,
    LANDING_CTA_LABEL,
    format_generation_created_at,
    format_generation_list_caption,
    format_generation_reference_caption,
)


def test_empty_generations_message() -> None:
    assert EMPTY_GENERATIONS_MESSAGE == "No Topic brief generations yet."


def test_landing_cta_label_names_destination() -> None:
    assert LANDING_CTA_LABEL == "Add a new Topic brief"


def test_format_generation_created_at_iso_utc() -> None:
    created = datetime(2026, 8, 12, 11, 30, 0, tzinfo=UTC)

    assert format_generation_created_at(created) == "2026-08-12T11:30:00+00:00"


def test_format_generation_reference_caption() -> None:
    topic_scope_key = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    assert (
        format_generation_reference_caption(topic_scope_key)
        == "Reference id: `aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee`"
    )


def test_format_generation_list_caption() -> None:
    topic_scope_key = uuid.UUID("11111111-2222-3333-4444-555555555555")
    created = datetime(2026, 8, 11, 12, 0, 0, tzinfo=UTC)

    assert format_generation_list_caption(
        "GLP-1 agonists in heart failure",
        created,
        topic_scope_key,
    ) == (
        "GLP-1 agonists in heart failure · 2026-08-11T12:00:00+00:00 · "
        "Reference id: `11111111-2222-3333-4444-555555555555`"
    )
