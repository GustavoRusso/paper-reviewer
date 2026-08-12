"""Topic intake Streamlit page (first step of topic brief generation)."""

from __future__ import annotations

import os
import uuid

import streamlit as st
from pydantic import ValidationError
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.schemas.topic_brief_generation.related_paper_search import (
    RelatedPaperSearchResult,
    SourceRun,
    SourceRunStatus,
)
from paper_reviewer.schemas.topic_brief_generation.topic_analysis import (
    TopicAnalysisResult,
)
from paper_reviewer.schemas.topic_brief_generation.topic_intake import TopicStatement
from paper_reviewer.topic_brief_generation.related_paper_search import (
    search_related_papers,
)
from paper_reviewer.topic_brief_generation.topic_analysis import analyze_topic_statement
from paper_reviewer.topic_brief_generation.topic_intake import (
    start_topic_brief_from_topic_intake,
)
from paper_reviewer.ui.navigation import streamlit_page_for

SESSION_KEY = "topic_statement"
PUBLIC_ID_KEY = "topic_brief_generation_public_id"
ANALYSIS_KEY = "topic_analysis_result"
SEARCH_KEY = "related_paper_search_result"
TRIAGE_RESULT_KEY = "retrieval_triage_result"
ARCHIVING_RESULT_KEY = "paper_archiving_result"
FULFILL_ENQUEUE_RESULT_KEY = "fulfill_papers_metadata_enqueue_result"


@st.cache_resource
def _session_factory() -> sessionmaker[Session]:
    """Shared SQLAlchemy session factory for the Streamlit process."""
    return create_session_factory(create_db_engine())


def _render_source_run_summary(run: SourceRun) -> None:
    facet_label = ", ".join(run.facet_ids) if run.facet_ids else "(none)"
    st.markdown(
        f"**{run.source_id}** — `{run.status.value}` — "
        f"{run.hit_count} hits (facets: {facet_label})"
    )
    if run.status == SourceRunStatus.error:
        st.error(run.error or "Paper source search failed.")
    elif run.status == SourceRunStatus.empty:
        st.caption("No paper candidates from this source.")


def render_topic_intake() -> None:
    """Render the Topic intake form and show the accepted topic statement."""
    st.title("New Topic brief")
    st.write(
        "This form starts Topic brief generation. After you submit a topic statement, "
        "the assistant analyzes its scope, searches paper sources for related papers, "
        "lets you triage which results to keep, builds a paper brief for each retained "
        "paper, and drafts a cited topic brief that explains what is currently known."
    )
    with st.form("topic_intake_form"):
        raw_text = st.text_area(
            "Define the topic and research scope",
            height=160,
            placeholder="e.g. GLP-1 agonists in heart failure with preserved ejection fraction",
        )
        submitted = st.form_submit_button("Submit")

    if submitted:
        try:
            with session_scope(_session_factory()) as session:
                topic_statement, generation = start_topic_brief_from_topic_intake(
                    session,
                    raw_text,
                )
        except ValidationError:
            st.error("Enter a non-empty topic statement.")
        except Exception:
            st.error("Could not start Topic brief generation. Try again.")
        else:
            st.session_state[SESSION_KEY] = topic_statement
            st.session_state[PUBLIC_ID_KEY] = generation.public_id
            st.session_state.pop(ANALYSIS_KEY, None)
            st.session_state.pop(SEARCH_KEY, None)
            st.session_state.pop(TRIAGE_RESULT_KEY, None)
            st.session_state.pop(ARCHIVING_RESULT_KEY, None)
            st.session_state.pop(FULFILL_ENQUEUE_RESULT_KEY, None)
            st.success("Topic brief generation started.")
            try:
                analysis = analyze_topic_statement(topic_statement.text)
            except Exception:
                st.error("Topic brief generation started, but topic analysis failed.")
            else:
                st.session_state[ANALYSIS_KEY] = analysis
                try:
                    with st.spinner("Searching paper sources…"):
                        search_result = search_related_papers(
                            analysis,
                            api_key=os.environ.get("NCBI_API_KEY") or None,
                        )
                except Exception:
                    st.error(
                        "Topic analysis succeeded, but related-paper search failed."
                    )
                else:
                    st.session_state[SEARCH_KEY] = search_result

    accepted: TopicStatement | None = st.session_state.get(SESSION_KEY)
    public_id: uuid.UUID | None = st.session_state.get(PUBLIC_ID_KEY)
    analysis: TopicAnalysisResult | None = st.session_state.get(ANALYSIS_KEY)
    search_result: RelatedPaperSearchResult | None = st.session_state.get(SEARCH_KEY)
    if accepted is not None:
        st.subheader("Accepted topic statement")
        st.write(accepted.text)
        if public_id is not None:
            st.caption(f"Reference id: `{public_id}`")
    if analysis is not None:
        st.subheader("Topic analysis")
        for facet in analysis.facets:
            st.write(f"**{facet.label}**")
            if facet.intent:
                st.caption(facet.intent)
            st.write(", ".join(facet.concepts))
    if search_result is not None:
        st.subheader("Related-paper search")
        if search_result.notes:
            st.caption(search_result.notes)
        for run in search_result.source_runs:
            _render_source_run_summary(run)
        count = len(search_result.candidates)
        st.caption(f"{count} paper candidate(s) ready for triage.")
        st.page_link(
            streamlit_page_for("retrieval_triage"),
            label="Continue to Retrieval triage",
        )
