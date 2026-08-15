"""Topic brief phase landing Streamlit page (v1 shell)."""

from __future__ import annotations

import streamlit as st

from paper_reviewer.ui.topic_scope_url import (
    parse_topic_scope_key,
    workflow_page_link,
)

MISSING_SCOPE_MESSAGE = (
    "Open Topic intake to create a Topic scope, then open Topic brief from "
    "the Topic scope hub."
)
NOT_BUILT_CAPTION = "Drafting the cited topic brief is not built yet."
GO_TO_TOPIC_INTAKE_LABEL = "Go to Topic intake"
GO_TO_TOPIC_SCOPE_LABEL = "Go to Topic scope"


def _render_missing_scope() -> None:
    st.info(MISSING_SCOPE_MESSAGE)
    workflow_page_link(
        "topic_intake",
        label=GO_TO_TOPIC_INTAKE_LABEL,
        topic_scope_key=None,
    )
    workflow_page_link(
        "topic_scope",
        label=GO_TO_TOPIC_SCOPE_LABEL,
        topic_scope_key=None,
    )


def render_topic_brief() -> None:
    """Render the Topic brief landing for the Topic scope in the URL."""
    st.title("Topic brief")
    topic_scope_key = parse_topic_scope_key(st.query_params)
    if topic_scope_key is None:
        _render_missing_scope()
        return

    st.caption(f"Reference id: `{topic_scope_key}`")
    st.caption(NOT_BUILT_CAPTION)
    workflow_page_link(
        "topic_scope",
        label=GO_TO_TOPIC_SCOPE_LABEL,
        topic_scope_key=topic_scope_key,
    )
