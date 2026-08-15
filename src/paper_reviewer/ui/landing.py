"""Landing page: entry point with Topic scope history and Create CTA."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

import streamlit as st
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.models.topic_brief_generation import (
    TopicScope,
    list_topic_scopes,
)
from paper_reviewer.ui.navigation import streamlit_page_for

LANDING_CTA_LABEL = "Add a Topic scope"
LANDING_CTA_PAGE_KEY = "topic_intake"
EMPTY_TOPIC_SCOPES_MESSAGE = "No Topic scopes yet."
TOPIC_SCOPES_SECTION_TITLE = "Topic scopes"


@st.cache_resource
def _session_factory() -> sessionmaker[Session]:
    """Shared SQLAlchemy session factory for the Streamlit process."""
    return create_session_factory(create_db_engine())


def landing_cta_page_key() -> str:
    """Return the navigation key targeted by the landing CTA."""
    return LANDING_CTA_PAGE_KEY


def format_topic_scope_created_at(created_at: datetime) -> str:
    """Return a stable ISO-8601 timestamp string for list display."""
    return created_at.isoformat()


def format_topic_scope_reference_caption(topic_scope_key: uuid.UUID) -> str:
    """Return the reference-id caption used on workflow pages."""
    return f"Reference id: `{topic_scope_key}`"


def format_topic_scope_list_caption(
    topic_statement: str,
    created_at: datetime,
    topic_scope_key: uuid.UUID,
) -> str:
    """Return one list-row caption for a Topic scope."""
    return (
        f"{topic_statement} · {format_topic_scope_created_at(created_at)} · "
        f"{format_topic_scope_reference_caption(topic_scope_key)}"
    )


def _render_topic_scope_list(topic_scopes: Sequence[TopicScope]) -> None:
    st.subheader(TOPIC_SCOPES_SECTION_TITLE)
    if not topic_scopes:
        st.caption(EMPTY_TOPIC_SCOPES_MESSAGE)
        return
    for topic_scope in topic_scopes:
        st.markdown(f"**{topic_scope.topic_statement}**")
        st.caption(
            f"{format_topic_scope_created_at(topic_scope.created_at)} · "
            f"{format_topic_scope_reference_caption(topic_scope.key)}"
        )


def render_landing() -> None:
    """Render the home page with Topic scope history and a Create CTA."""
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
            topic_scopes = list(list_topic_scopes(session))
    except Exception:
        st.error("Could not load Topic scopes. Try again.")
    else:
        _render_topic_scope_list(topic_scopes)
