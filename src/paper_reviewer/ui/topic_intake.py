"""Topic intake Streamlit page (create a Topic scope)."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

import streamlit as st
from pydantic import ValidationError
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.schemas.topic_scope.topic_intake import TopicStatement
from paper_reviewer.topic_scope.topic_intake import (
    start_topic_scope_from_topic_intake,
)
from paper_reviewer.ui.topic_scope_url import workflow_switch_page

SESSION_KEY = "topic_statement"
ANALYSIS_KEY = "topic_analysis_result"
SEARCH_KEY = "search_external_sources_result"
SEARCH_TOPIC_SCOPE_KEY = "search_external_sources_topic_scope_key"
ARCHIVING_RESULT_KEY = "paper_archiving_result"
PAPER_INGEST_ENQUEUE_RESULT_KEY = "paper_ingest_enqueue_result"


def begin_topic_intake_session(
    state: MutableMapping[str, Any],
    *,
    topic_statement: TopicStatement,
) -> None:
    """Drop all session keys, then store the new topic statement."""
    state.clear()
    state[SESSION_KEY] = topic_statement


@st.cache_resource
def _session_factory() -> sessionmaker[Session]:
    """Shared SQLAlchemy session factory for the Streamlit process."""
    return create_session_factory(create_db_engine())


def render_topic_intake() -> None:
    """Render the Topic intake form and switch to Topic analysis on success."""
    st.title("Topic intake")
    st.write("Declare a topic statement to create a Topic scope.")
    with st.form("topic_intake_form"):
        raw_text = st.text_area(
            "Define the topic and research scope",
            height=160,
            placeholder="e.g. GLP-1 agonists in heart failure with preserved ejection fraction",
        )
        submitted = st.form_submit_button("Submit", type="primary")

    if submitted:
        try:
            with session_scope(_session_factory()) as session:
                topic_statement, topic_scope = start_topic_scope_from_topic_intake(
                    session,
                    raw_text,
                )
        except ValidationError:
            st.error("Enter a non-empty topic statement.")
        except Exception:
            st.error("Could not start Topic intake. Try again.")
        else:
            begin_topic_intake_session(
                st.session_state,
                topic_statement=topic_statement,
            )
            workflow_switch_page(
                "topic_analysis",
                topic_scope_key=topic_scope.key,
            )
