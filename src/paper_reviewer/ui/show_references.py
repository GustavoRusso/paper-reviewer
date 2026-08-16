"""Show references Streamlit page (list is empty until persistence lands)."""

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
    "Open Topic intake to create a Topic scope, then open Show references "
    "from References selection."
)
EMPTY_REFERENCES_CAPTION = "This Topic scope has no References yet."
GO_TO_TOPIC_INTAKE_LABEL = "Go to Topic intake"
GO_TO_TOPIC_SCOPE_LABEL = "Go to Topic scope"
CONTINUE_TO_ADD_REFERENCE_LABEL = "Continue to Add reference"
GO_TO_REFERENCES_SELECTION_LABEL = "Go to References selection"


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


def _render_empty_list(*, topic_scope_key: UUID) -> None:
    st.caption(EMPTY_REFERENCES_CAPTION)
    workflow_page_link(
        "add_reference",
        label=CONTINUE_TO_ADD_REFERENCE_LABEL,
        topic_scope_key=topic_scope_key,
    )
    workflow_page_link(
        "topic_scope",
        label=GO_TO_TOPIC_SCOPE_LABEL,
        topic_scope_key=topic_scope_key,
    )
    workflow_page_link(
        "references_selection",
        label=GO_TO_REFERENCES_SELECTION_LABEL,
        topic_scope_key=topic_scope_key,
    )


def render_show_references() -> None:
    """Render Show references for the Topic scope in the URL."""
    topic_scope_key = parse_topic_scope_key(st.query_params)
    render_references_selection_header(
        current_page_key="show_references",
        topic_scope_key=topic_scope_key,
    )
    st.header("Show references")

    if topic_scope_key is None:
        _render_missing_scope(topic_scope_key=None)
        return

    _render_empty_list(topic_scope_key=topic_scope_key)
