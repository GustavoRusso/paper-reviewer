"""Shared Streamlit display for one topic facet (analysis page and hub)."""

from __future__ import annotations

import streamlit as st

from paper_reviewer.schemas.topic_brief_generation.topic_analysis import TopicFacet


def render_topic_facet(facet: TopicFacet) -> None:
    """Show label, optional intent, and concepts for one facet."""
    st.write(f"**{facet.label}**")
    if facet.intent:
        st.caption(facet.intent)
    st.write(", ".join(facet.concepts))
