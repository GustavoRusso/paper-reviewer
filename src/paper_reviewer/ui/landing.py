"""Landing page: entry point with Topic brief generation history and Create CTA."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

import streamlit as st
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.models.topic_brief_generation import (
    TopicBriefGeneration,
    list_topic_brief_generations,
)
from paper_reviewer.ui.navigation import streamlit_page_for

LANDING_CTA_LABEL = "Go to New Topic brief"
LANDING_CTA_PAGE_KEY = "new_topic_brief"
EMPTY_GENERATIONS_MESSAGE = "No Topic brief generations yet."
GENERATIONS_SECTION_TITLE = "Topic brief generations"


@st.cache_resource
def _session_factory() -> sessionmaker[Session]:
    """Shared SQLAlchemy session factory for the Streamlit process."""
    return create_session_factory(create_db_engine())


def landing_cta_page_key() -> str:
    """Return the navigation key targeted by the landing CTA."""
    return LANDING_CTA_PAGE_KEY


def format_generation_created_at(created_at: datetime) -> str:
    """Return a stable ISO-8601 timestamp string for list display."""
    return created_at.isoformat()


def format_generation_reference_caption(public_id: uuid.UUID) -> str:
    """Return the reference-id caption used on workflow pages."""
    return f"Reference id: `{public_id}`"


def format_generation_list_caption(
    topic_statement: str,
    created_at: datetime,
    public_id: uuid.UUID,
) -> str:
    """Return one list-row caption for a Topic brief generation."""
    return (
        f"{topic_statement} · {format_generation_created_at(created_at)} · "
        f"{format_generation_reference_caption(public_id)}"
    )


def _render_generation_list(generations: Sequence[TopicBriefGeneration]) -> None:
    st.subheader(GENERATIONS_SECTION_TITLE)
    if not generations:
        st.caption(EMPTY_GENERATIONS_MESSAGE)
        return
    for generation in generations:
        st.markdown(f"**{generation.topic_statement}**")
        st.caption(
            f"{format_generation_created_at(generation.created_at)} · "
            f"{format_generation_reference_caption(generation.public_id)}"
        )


def render_landing() -> None:
    """Render the home page with generation history and a Create CTA."""
    st.title("Paper Reviewer")
    st.write(
        "Explore biomedical and life sciences topics. "
        "Start from a topic statement and produce a cited topic brief "
        "grounded in scientific papers."
    )
    st.page_link(
        streamlit_page_for(landing_cta_page_key()),
        label=LANDING_CTA_LABEL,
    )
    try:
        with session_scope(_session_factory()) as session:
            generations = list(list_topic_brief_generations(session))
    except Exception:
        st.error("Could not load Topic brief generations. Try again.")
    else:
        _render_generation_list(generations)
