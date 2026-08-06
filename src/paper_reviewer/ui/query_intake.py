"""Query intake Streamlit page (first step of topic brief generation)."""

from __future__ import annotations

import streamlit as st
from pydantic import ValidationError

from paper_reviewer.schemas.query_intake import ResearchQuery, accept_query_intake

SESSION_KEY = "research_query"


def render_query_intake() -> None:
    """Render the Query intake form and show the accepted research query."""
    st.set_page_config(
        page_title="New Topic brief generation", page_icon=None, layout="centered"
    )
    st.title("Topic brief generation")
    st.write(
        "Start a cited topic brief by completing Query intake: "
        "provide a research query specifying what to investigate."
    )

    st.subheader("Query intake")
    with st.form("query_intake_form"):
        raw_text = st.text_area(
            "Research query",
            height=160,
            placeholder="e.g. GLP-1 agonists in heart failure with preserved ejection fraction",
        )
        submitted = st.form_submit_button("Submit")

    if submitted:
        try:
            research_query = accept_query_intake(raw_text)
        except ValidationError:
            st.error("Enter a non-empty research query.")
        else:
            st.session_state[SESSION_KEY] = research_query
            st.success("Research query accepted.")

    accepted: ResearchQuery | None = st.session_state.get(SESSION_KEY)
    if accepted is not None:
        st.subheader("Accepted research query")
        st.write(accepted.text)
