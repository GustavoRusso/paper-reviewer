"""Add reference Streamlit page (v1 stub; attach is not built yet)."""

from __future__ import annotations

from uuid import UUID

import streamlit as st

from paper_reviewer.ui.references_selection import (
    render_references_selection_header,
)
from paper_reviewer.ui.topic_scope_url import (
    parse_topic_scope_key,
    workflow_page_link,
)

MISSING_SCOPE_MESSAGE = (
    "Open Topic intake to create a Topic scope, then open Add reference "
    "from References selection."
)
NOT_BUILT_CAPTION = (
    "Attaching References from local search results is not built yet."
)
GO_TO_TOPIC_INTAKE_LABEL = "Go to Topic intake"
GO_TO_TOPIC_SCOPE_LABEL = "Go to Topic scope"
GO_TO_SHOW_REFERENCES_LABEL = "Go to Show references"


def _render_missing_scope(*, topic_scope_key: UUID | None) -> None:
    st.info(MISSING_SCOPE_MESSAGE)
    workflow_page_link(
        "topic_intake",
        label=GO_TO_TOPIC_INTAKE_LABEL,
        topic_scope_key=topic_scope_key,
    )
    workflow_page_link(
        "topic_scope",
        label=GO_TO_TOPIC_SCOPE_LABEL,
        topic_scope_key=topic_scope_key,
    )


def render_add_reference() -> None:
    """Render the Add reference stub for the Topic scope in the URL."""
    topic_scope_key = parse_topic_scope_key(st.query_params)
    render_references_selection_header(
        current_page_key="add_reference",
        topic_scope_key=topic_scope_key,
    )
    st.header("Add reference")

    if topic_scope_key is None:
        _render_missing_scope(topic_scope_key=None)
        return

    st.caption(NOT_BUILT_CAPTION)
    workflow_page_link(
        "show_references",
        label=GO_TO_SHOW_REFERENCES_LABEL,
        topic_scope_key=topic_scope_key,
    )
