"""Related-paper search Streamlit page (auto-run lands in a later slice)."""

from __future__ import annotations

import streamlit as st

from paper_reviewer.ui.paper_ingestion import render_paper_ingestion_header
from paper_reviewer.ui.topic_scope_url import parse_topic_scope_key


def render_related_paper_search() -> None:
    """Render Related-paper search (search auto-run is not in this slice)."""
    topic_scope_key = parse_topic_scope_key(st.query_params)
    render_paper_ingestion_header(
        current_page_key="related_paper_search",
        topic_scope_key=topic_scope_key,
    )
    st.title("Related-paper search")
