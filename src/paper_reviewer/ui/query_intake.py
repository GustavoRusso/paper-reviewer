"""Query intake Streamlit page."""

from __future__ import annotations

import streamlit as st
from pydantic import ValidationError

from paper_reviewer.schemas.query_intake import ResearchQuery, accept_query_intake

SESSION_KEY = "research_query"


def render_query_intake() -> None:
    """Render the Query intake form and show the accepted research query."""
    st.set_page_config(page_title="Query intake", page_icon=None, layout="centered")
    st.title("Query intake")
    st.write(
        "Provide a research query specifying what to investigate. "
        "This is the first step toward a cited topic brief."
    )

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
