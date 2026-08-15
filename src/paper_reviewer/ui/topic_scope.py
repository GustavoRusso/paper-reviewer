"""Topic scope hub Streamlit page (statement, facets, later phases)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

import streamlit as st
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.models.topic_brief_generation import get_topic_scope_by_key
from paper_reviewer.topic_brief_generation.topic_analysis import (
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
CONTINUE_TO_PAPER_INGESTION_LABEL = "Continue to Paper ingestion"
CONTINUE_TO_PAPER_SEARCH_LABEL = "Continue to Paper search"
CONTINUE_TO_TOPIC_BRIEF_LABEL = "Continue to Topic brief"
PHASE_LANDING_PAGE_KEYS = (
    "paper_ingestion",
    "paper_search",
    "topic_brief",
)

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


def _render_phase_links(*, topic_scope_key: UUID) -> None:
    labels = {
        "paper_ingestion": CONTINUE_TO_PAPER_INGESTION_LABEL,
        "paper_search": CONTINUE_TO_PAPER_SEARCH_LABEL,
        "topic_brief": CONTINUE_TO_TOPIC_BRIEF_LABEL,
    }
    for page_key in PHASE_LANDING_PAGE_KEYS:
        workflow_page_link(
            page_key,
            label=labels[page_key],
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
    _render_phase_links(topic_scope_key=topic_scope_key)
