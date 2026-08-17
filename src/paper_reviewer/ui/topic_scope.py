"""Topic scope hub Streamlit page (statement, facets, later phases)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

import streamlit as st
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.models.topic_scope import (
    count_references_for_scope,
    get_topic_scope_by_key,
)
from paper_reviewer.topic_scope.topic_analysis import (
    load_topic_analysis_result,
)
from paper_reviewer.ui.topic_facet_display import render_topic_facet
from paper_reviewer.ui.topic_scope_url import (
    parse_topic_scope_key,
    workflow_page_link,
)

MISSING_SCOPE_MESSAGE = (
    "Open Topic intake to create a Topic scope, then open it here."
)
INCOMPLETE_MESSAGE = (
    "This Topic scope has no topic facets yet. "
    "Open Topic analysis to extract them."
)
GO_TO_TOPIC_INTAKE_LABEL = "Go to Topic intake"
GO_TO_TOPIC_ANALYSIS_LABEL = "Go to Topic analysis"
HUB_REFERENCES_TITLE = "References"
HUB_TOPIC_BRIEF_TITLE = "Topic Brief"
HUB_ACTIONS_TITLE = "Actions"
HUB_REFERENCES_PAGE_KEY = "show_references"
HUB_TOPIC_BRIEF_PAGE_KEY = "topic_brief_generation"
HUB_EXTERNAL_SOURCES_INGESTION_PAGE_KEY = "external_sources_ingestion"
HUB_TOPIC_BRIEF_LABEL = "Topic brief generation"
HUB_EXTERNAL_SOURCES_INGESTION_LABEL = "External sources ingestion"

TopicScopeHubView = Literal["missing_scope", "incomplete", "ready"]


@st.cache_resource
def _session_factory() -> sessionmaker[Session]:
    """Shared SQLAlchemy session factory for the Streamlit process."""
    return create_session_factory(create_db_engine())


def topic_scope_hub_view(
    *,
    topic_scope_key: UUID | None,
    has_scope: bool,
    has_facets: bool,
) -> TopicScopeHubView:
    """Return which hub state to render for the current Topic scope."""
    if topic_scope_key is None or not has_scope:
        return "missing_scope"
    if not has_facets:
        return "incomplete"
    return "ready"


def _render_missing_scope() -> None:
    st.info(MISSING_SCOPE_MESSAGE)
    workflow_page_link(
        "topic_intake",
        label=GO_TO_TOPIC_INTAKE_LABEL,
        topic_scope_key=None,
    )


def _render_incomplete(*, topic_scope_key: UUID) -> None:
    st.info(INCOMPLETE_MESSAGE)
    workflow_page_link(
        "topic_analysis",
        label=GO_TO_TOPIC_ANALYSIS_LABEL,
        topic_scope_key=topic_scope_key,
    )


def format_hub_reference_count_label(count: int) -> str:
    """Return the References pane link label (the decimal count)."""
    return str(count)


def _render_action_row(*, topic_scope_key: UUID, reference_count: int) -> None:
    with st.container(horizontal=True, border=False):
        with st.container(border=False, width="stretch"):
            st.subheader(HUB_REFERENCES_TITLE)
            workflow_page_link(
                HUB_REFERENCES_PAGE_KEY,
                label=format_hub_reference_count_label(reference_count),
                topic_scope_key=topic_scope_key,
            )
        with st.container(border=False, width="stretch"):
            st.subheader(HUB_TOPIC_BRIEF_TITLE)
            workflow_page_link(
                HUB_TOPIC_BRIEF_PAGE_KEY,
                label=HUB_TOPIC_BRIEF_LABEL,
                topic_scope_key=topic_scope_key,
            )
        with st.container(border=False, width="stretch"):
            st.subheader(HUB_ACTIONS_TITLE)
            workflow_page_link(
                HUB_EXTERNAL_SOURCES_INGESTION_PAGE_KEY,
                label=HUB_EXTERNAL_SOURCES_INGESTION_LABEL,
                topic_scope_key=topic_scope_key,
            )


def render_topic_scope() -> None:
    """Render the Topic scope hub for the Topic scope in the URL."""
    st.title("Topic scope")
    topic_scope_key = parse_topic_scope_key(st.query_params)
    if topic_scope_key is None:
        _render_missing_scope()
        return

    try:
        with session_scope(_session_factory()) as session:
            topic_scope = get_topic_scope_by_key(session, topic_scope_key)
            if topic_scope is None:
                _render_missing_scope()
                return
            analysis = load_topic_analysis_result(session, topic_scope)
            topic_statement = topic_scope.topic_statement
            reference_count = count_references_for_scope(
                session, topic_scope.id
            )
    except Exception:
        st.error("Could not load this Topic scope. Try again.")
        return

    view = topic_scope_hub_view(
        topic_scope_key=topic_scope_key,
        has_scope=True,
        has_facets=bool(analysis.facets),
    )
    if view == "incomplete":
        _render_incomplete(topic_scope_key=topic_scope_key)
        return

    st.caption(f"Reference id: `{topic_scope_key}`")
    st.subheader("Topic statement")
    st.write(topic_statement)
    st.subheader("Topic facets")
    for facet in analysis.facets:
        render_topic_facet(facet)
    _render_action_row(
        topic_scope_key=topic_scope_key,
        reference_count=reference_count,
    )
