"""Landing page: entry point with a CTA to start a new Topic brief."""

from __future__ import annotations

import streamlit as st

from paper_reviewer.ui.navigation import streamlit_page_for

LANDING_CTA_LABEL = "Create a new Topic brief"
LANDING_CTA_PAGE_KEY = "new_topic_brief"


def landing_cta_page_key() -> str:
    """Return the navigation key targeted by the landing CTA."""
    return LANDING_CTA_PAGE_KEY


def render_landing() -> None:
    """Render the home landing page with a link to create a Topic brief."""
    st.title("Paper Reviewer")
    st.write(
        "Explore biomedical and life sciences topics. "
        "Start from a research query and produce a cited topic brief "
        "grounded in scientific papers."
    )
    st.page_link(
        streamlit_page_for(landing_cta_page_key()),
        label=LANDING_CTA_LABEL,
    )
