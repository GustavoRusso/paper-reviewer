"""Paper ingestion phase landing Streamlit page."""

from __future__ import annotations

import streamlit as st

from paper_reviewer.ui.topic_scope_url import (
    parse_topic_scope_key,
    workflow_page_link,
)

INTRO_TEXT = (
    "This phase searches paper sources and ingests papers for this Topic scope."
)
MISSING_SCOPE_MESSAGE = (
    "Open Topic intake to create a Topic scope, then open Paper ingestion from "
    "the Topic scope hub."
)
GO_TO_TOPIC_INTAKE_LABEL = "Go to Topic intake"
GO_TO_TOPIC_SCOPE_LABEL = "Go to Topic scope"
RELATED_PAPER_SEARCH_PAGE_KEY = "related_paper_search"
CONTINUE_TO_RELATED_PAPER_SEARCH_LABEL = "Continue to Related-paper search"
CONTINUE_TO_PAPER_ARCHIVING_LABEL = "Continue to Paper archiving"
CONTINUE_TO_FULFILL_PAPERS_METADATA_LABEL = "Continue to Fulfill papers metadata"
CONTINUE_TO_GENERATE_PAPER_BRIEF_LABEL = "Continue to Generate paper brief"


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


def render_paper_ingestion() -> None:
    """Render the Paper ingestion landing for the Topic scope in the URL."""
    st.title("Paper ingestion")
    topic_scope_key = parse_topic_scope_key(st.query_params)
    if topic_scope_key is None:
        _render_missing_scope()
        return

    st.caption(f"Reference id: `{topic_scope_key}`")
    st.write(INTRO_TEXT)
    workflow_page_link(
        RELATED_PAPER_SEARCH_PAGE_KEY,
        label=CONTINUE_TO_RELATED_PAPER_SEARCH_LABEL,
        topic_scope_key=topic_scope_key,
    )
    workflow_page_link(
        "paper_archiving",
        label=CONTINUE_TO_PAPER_ARCHIVING_LABEL,
        topic_scope_key=topic_scope_key,
    )
    workflow_page_link(
        "fulfill_papers_metadata",
        label=CONTINUE_TO_FULFILL_PAPERS_METADATA_LABEL,
        topic_scope_key=topic_scope_key,
    )
    workflow_page_link(
        "generate_paper_brief",
        label=CONTINUE_TO_GENERATE_PAPER_BRIEF_LABEL,
        topic_scope_key=topic_scope_key,
    )
