"""Retrieval triage Streamlit page (review and confirm search candidates)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping
from uuid import UUID

import streamlit as st
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.schemas.topic_brief_generation.paper_archiving import (
    PaperArchivingResult,
)
from paper_reviewer.schemas.topic_brief_generation.related_paper_search import (
    PaperCandidate,
    RelatedPaperSearchResult,
    SourceRun,
    SourceRunStatus,
)
from paper_reviewer.schemas.topic_brief_generation.topic_intake import TopicStatement
from paper_reviewer.topic_brief_generation.paper_archiving import archive_papers
from paper_reviewer.topic_brief_generation.retrieval_triage import (
    confirm_retrieval_triage,
)
from paper_reviewer.ui.navigation import streamlit_page_for
from paper_reviewer.ui.topic_intake import (
    ARCHIVING_RESULT_KEY,
    PUBLIC_ID_KEY,
    SEARCH_KEY,
    SESSION_KEY,
    TRIAGE_RESULT_KEY,
)

CONFIRM_BUTTON_LABEL = "Continue to paper archiving"


@st.cache_resource
def _session_factory() -> sessionmaker[Session]:
    """Shared SQLAlchemy session factory for the Streamlit process."""
    return create_session_factory(create_db_engine())


def triage_prerequisites_met(state: Mapping[str, Any]) -> bool:
    """Return True when generation id and search result are in session state."""
    return state.get(PUBLIC_ID_KEY) is not None and state.get(SEARCH_KEY) is not None


def format_paper_archiving_summary(result: PaperArchivingResult) -> str:
    """Short success line for inline paper archiving after triage confirm."""
    return (
        f"Paper archiving finished: {len(result.papers)} paper(s), "
        f"{len(result.skipped)} skipped, {len(result.errors)} error(s)."
    )


def _render_source_run_status(run: SourceRun) -> None:
    facet_label = ", ".join(run.facet_ids) if run.facet_ids else "(none)"
    st.markdown(
        f"**{run.source_id}** — `{run.status.value}` — "
        f"{run.hit_count} hits (facets: {facet_label})"
    )
    if run.status == SourceRunStatus.error:
        st.error(run.error or "Paper source search failed.")
    elif run.status == SourceRunStatus.empty:
        st.caption("No paper candidates from this source.")


def _render_candidate(candidate: PaperCandidate) -> None:
    authors = ", ".join(candidate.authors) if candidate.authors else "—"
    journal = candidate.journal or "—"
    year = (
        str(candidate.published_year)
        if candidate.published_year is not None
        else "—"
    )
    st.markdown(f"**[{candidate.title}]({candidate.url})**")
    doi_part = f" · DOI `{candidate.doi}`" if candidate.doi else ""
    st.caption(
        f"{authors} · {journal} · {year} · "
        f"`{candidate.source_uid}` · facet `{candidate.facet_id}`{doi_part}"
    )


def render_retrieval_triage() -> None:
    """Render the Retrieval triage review and confirm page."""
    st.title("Retrieval triage")

    if not triage_prerequisites_met(st.session_state):
        st.info(
            "Run related-paper search from New Topic brief before triage. "
            "Open that page, submit a topic statement, and wait for search to finish."
        )
        st.page_link(
            streamlit_page_for("new_topic_brief"),
            label="Go to New Topic brief",
        )
        return

    public_id: UUID = st.session_state[PUBLIC_ID_KEY]
    search_result: RelatedPaperSearchResult = st.session_state[SEARCH_KEY]
    topic: TopicStatement | None = st.session_state.get(SESSION_KEY)

    st.caption(f"Reference id: `{public_id}`")
    if topic is not None:
        snippet = topic.text if len(topic.text) <= 200 else f"{topic.text[:197]}..."
        st.write(snippet)

    st.subheader("Source runs")
    if search_result.notes:
        st.caption(search_result.notes)
    for run in search_result.source_runs:
        _render_source_run_status(run)

    candidates = search_result.candidates
    count = len(candidates)
    st.subheader("Candidates")
    if count == 0:
        st.caption(
            "Search returned no retainable papers. "
            "You can still continue; paper archiving will be a no-op."
        )
    else:
        st.caption(f"{count} papers to archive")
        for candidate in candidates:
            _render_candidate(candidate)

    if st.button(CONFIRM_BUTTON_LABEL, type="primary"):
        triage_result = confirm_retrieval_triage(search_result).model_copy(
            update={"confirmed_at": datetime.now(UTC)}
        )
        st.session_state[TRIAGE_RESULT_KEY] = triage_result
        try:
            with session_scope(_session_factory()) as session:
                archiving_result = archive_papers(session, triage_result.retained)
        except Exception:
            st.error("Triage confirmed, but paper archiving failed. Try again.")
        else:
            st.session_state[ARCHIVING_RESULT_KEY] = archiving_result
            st.success(
                f"Confirmed {len(triage_result.retained)} paper(s) for archiving. "
                f"{format_paper_archiving_summary(archiving_result)}"
            )

    archived: PaperArchivingResult | None = st.session_state.get(ARCHIVING_RESULT_KEY)
    if archived is not None:
        st.subheader("Paper archiving")
        st.write(format_paper_archiving_summary(archived))
