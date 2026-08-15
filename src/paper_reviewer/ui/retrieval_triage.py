"""Retrieval triage Streamlit page (review and confirm search candidates)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping
from uuid import UUID

import streamlit as st

from paper_reviewer.schemas.topic_brief_generation.related_paper_search import (
    PaperCandidate,
    RelatedPaperSearchResult,
    SourceRun,
    SourceRunStatus,
)
from paper_reviewer.schemas.topic_brief_generation.topic_intake import TopicStatement
from paper_reviewer.topic_brief_generation.retrieval_triage import (
    confirm_retrieval_triage,
)
from paper_reviewer.ui.topic_scope_url import (
    parse_topic_scope_public_id,
    workflow_page_link,
)
from paper_reviewer.ui.new_topic_brief import (
    ARCHIVING_RESULT_KEY,
    FULFILL_ENQUEUE_RESULT_KEY,
    GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY,
    SEARCH_KEY,
    SESSION_KEY,
    TRIAGE_RESULT_KEY,
)

CONFIRM_BUTTON_LABEL = "Confirm for paper archiving"


def triage_prerequisites_met(
    state: Mapping[str, Any],
    *,
    public_id: UUID | None,
) -> bool:
    """Return True when generation id is in the URL and search result is in session."""
    return public_id is not None and state.get(SEARCH_KEY) is not None


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

    public_id = parse_topic_scope_public_id(st.query_params)
    if not triage_prerequisites_met(st.session_state, public_id=public_id):
        st.info(
            "Run related-paper search from New Topic brief before triage. "
            "Open that page, submit a topic statement, and wait for search to finish."
        )
        workflow_page_link(
            "new_topic_brief",
            label="Go to New Topic brief",
            public_id=public_id,
        )
        return

    assert public_id is not None
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
            "You can still confirm; paper archiving will be a no-op."
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
        st.session_state.pop(ARCHIVING_RESULT_KEY, None)
        st.session_state.pop(FULFILL_ENQUEUE_RESULT_KEY, None)
        st.session_state.pop(GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY, None)
        st.success(
            f"Confirmed {len(triage_result.retained)} paper(s) for archiving."
        )

    if st.session_state.get(TRIAGE_RESULT_KEY) is not None:
        workflow_page_link(
            "paper_archiving",
            label="Continue to Paper archiving",
            public_id=public_id,
        )
