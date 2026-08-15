"""Search external sources Streamlit page (auto-run search from DB facets)."""

from __future__ import annotations

import os
from collections.abc import MutableMapping
from typing import Any, Mapping
from uuid import UUID

import streamlit as st
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.models.topic_brief_generation import get_topic_scope_by_key
from paper_reviewer.schemas.topic_brief_generation.search_external_sources import (
    SearchExternalSourcesResult,
    SourceRun,
    SourceRunStatus,
)
from paper_reviewer.schemas.topic_brief_generation.topic_analysis import (
    TopicAnalysisResult,
)
from paper_reviewer.topic_brief_generation.search_external_sources import (
    search_external_sources,
)
from paper_reviewer.topic_brief_generation.topic_analysis import (
    load_topic_analysis_result,
)
from paper_reviewer.ui.paper_ingestion import render_paper_ingestion_header
from paper_reviewer.ui.topic_intake import (
    ARCHIVING_RESULT_KEY,
    FULFILL_ENQUEUE_RESULT_KEY,
    GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY,
    SEARCH_KEY,
    SEARCH_TOPIC_SCOPE_KEY,
)
from paper_reviewer.ui.topic_scope_url import (
    parse_topic_scope_key,
    workflow_page_link,
)

MISSING_PREREQUISITES_MESSAGE = (
    "Open Topic analysis to create topic facets for this Topic scope, "
    "then return here to search external sources."
)
GO_TO_TOPIC_ANALYSIS_LABEL = "Go to Topic analysis"
GO_TO_TOPIC_SCOPE_LABEL = "Go to Topic scope"
CONTINUE_TO_PAPER_ARCHIVING_LABEL = "Continue to Paper archiving"


@st.cache_resource
def _session_factory() -> sessionmaker[Session]:
    """Shared SQLAlchemy session factory for the Streamlit process."""
    return create_session_factory(create_db_engine())


def search_cache_matches(
    state: Mapping[str, Any],
    *,
    topic_scope_key: UUID | None,
) -> bool:
    """Return True when session has a search result for this Topic scope key."""
    if topic_scope_key is None:
        return False
    if state.get(SEARCH_KEY) is None:
        return False
    cached_key = state.get(SEARCH_TOPIC_SCOPE_KEY)
    return cached_key is not None and cached_key == str(topic_scope_key)


def clear_downstream_ingest_caches(state: MutableMapping[str, Any]) -> None:
    """Clear session caches for steps after Search external sources."""
    state.pop(ARCHIVING_RESULT_KEY, None)
    state.pop(FULFILL_ENQUEUE_RESULT_KEY, None)
    state.pop(GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY, None)


def _render_missing_prerequisites(*, topic_scope_key: UUID | None) -> None:
    st.info(MISSING_PREREQUISITES_MESSAGE)
    workflow_page_link(
        "topic_analysis",
        label=GO_TO_TOPIC_ANALYSIS_LABEL,
        topic_scope_key=topic_scope_key,
    )
    workflow_page_link(
        "topic_scope",
        label=GO_TO_TOPIC_SCOPE_LABEL,
        topic_scope_key=topic_scope_key,
    )


def _render_source_run_status(run: SourceRun) -> None:
    facet_label = ", ".join(run.facet_ids) if run.facet_ids else "(none)"
    st.markdown(
        f"**{run.source_id}** — `{run.status.value}` — "
        f"{run.hit_count} hits (facets: {facet_label})"
    )
    if run.status == SourceRunStatus.error:
        st.error(run.error or "External source search failed.")
    elif run.status == SourceRunStatus.empty:
        st.caption("No paper candidates from this source.")


def _render_result(result: SearchExternalSourcesResult) -> None:
    st.subheader("Source runs")
    if result.notes:
        st.caption(result.notes)
    if not result.source_runs:
        st.caption("No external sources ran.")
    else:
        for run in result.source_runs:
            _render_source_run_status(run)

    count = len(result.candidates)
    st.subheader("Candidates")
    st.caption(f"{count} paper candidate(s) ready for paper archiving.")


def render_search_external_sources() -> None:
    """Render Search external sources: load facets from DB and auto-run search."""
    topic_scope_key = parse_topic_scope_key(st.query_params)
    render_paper_ingestion_header(
        current_page_key="search_external_sources",
        topic_scope_key=topic_scope_key,
    )
    st.header("Search external sources")

    if topic_scope_key is None:
        _render_missing_prerequisites(topic_scope_key=None)
        return

    analysis = TopicAnalysisResult(facets=[])
    try:
        with session_scope(_session_factory()) as session:
            topic_scope = get_topic_scope_by_key(session, topic_scope_key)
            if topic_scope is None:
                _render_missing_prerequisites(topic_scope_key=topic_scope_key)
                return
            analysis = load_topic_analysis_result(session, topic_scope)
    except Exception:
        st.error("Could not load Topic scope facets. Try again.")
        return

    if not analysis.facets:
        _render_missing_prerequisites(topic_scope_key=topic_scope_key)
        return

    st.caption(f"Reference id: `{topic_scope_key}`")

    if search_cache_matches(st.session_state, topic_scope_key=topic_scope_key):
        result: SearchExternalSourcesResult = st.session_state[SEARCH_KEY]
        _render_result(result)
        workflow_page_link(
            "paper_archiving",
            label=CONTINUE_TO_PAPER_ARCHIVING_LABEL,
            topic_scope_key=topic_scope_key,
        )
        return

    clear_downstream_ingest_caches(st.session_state)
    try:
        with st.spinner("Searching external sources…"):
            result = search_external_sources(
                analysis,
                api_key=os.environ.get("NCBI_API_KEY") or None,
            )
    except Exception:
        st.error("Search external sources failed. Try again.")
        return

    st.session_state[SEARCH_KEY] = result
    st.session_state[SEARCH_TOPIC_SCOPE_KEY] = str(topic_scope_key)
    _render_result(result)
    workflow_page_link(
        "paper_archiving",
        label=CONTINUE_TO_PAPER_ARCHIVING_LABEL,
        topic_scope_key=topic_scope_key,
    )
