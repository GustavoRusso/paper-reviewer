"""Topic analysis Streamlit page (extract and show topic facets)."""

from __future__ import annotations

import streamlit as st
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.models.topic_scope import get_topic_scope_by_key
from paper_reviewer.schemas.topic_scope.topic_analysis import (
    TopicAnalysisResult,
)
from paper_reviewer.topic_scope.topic_analysis import (
    load_topic_analysis_result,
    run_topic_analysis,
)
from paper_reviewer.ui.topic_facet_display import render_topic_facet
from paper_reviewer.ui.topic_scope_url import (
    parse_topic_scope_key,
    workflow_page_link,
)


@st.cache_resource
def _session_factory() -> sessionmaker[Session]:
    """Shared SQLAlchemy session factory for the Streamlit process."""
    return create_session_factory(create_db_engine())


def _render_missing_scope() -> None:
    st.info("Open Topic intake to create a Topic scope, then analyze it here.")
    workflow_page_link(
        "topic_intake",
        label="Go to Topic intake",
        topic_scope_key=None,
    )


def render_topic_analysis() -> None:
    """Render Topic analysis for the Topic scope in the URL."""
    st.title("Topic analysis")
    topic_scope_key = parse_topic_scope_key(st.query_params)
    if topic_scope_key is None:
        _render_missing_scope()
        return

    analysis = TopicAnalysisResult(facets=[])
    try:
        with session_scope(_session_factory()) as session:
            topic_scope = get_topic_scope_by_key(session, topic_scope_key)
            if topic_scope is None:
                _render_missing_scope()
                return
            analysis = load_topic_analysis_result(session, topic_scope)
            if not analysis.facets:
                with st.spinner("Analyzing topic…"):
                    analysis = run_topic_analysis(session, topic_scope)
    except Exception:
        st.error("Topic analysis failed. Try again.")
        return

    if not analysis.facets:
        return

    st.caption(f"Reference id: `{topic_scope_key}`")
    for facet in analysis.facets:
        render_topic_facet(facet)
    workflow_page_link(
        "topic_scope",
        label="Continue to Topic scope",
        topic_scope_key=topic_scope_key,
    )
