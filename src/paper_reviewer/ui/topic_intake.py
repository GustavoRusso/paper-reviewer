"""Topic intake Streamlit page (first step of topic brief generation)."""

from __future__ import annotations

import uuid

import streamlit as st
from pydantic import ValidationError
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.models.topic_brief_generation import start_topic_brief_from_topic_intake
from paper_reviewer.schemas.topic_intake import TopicStatement

SESSION_KEY = "topic_statement"
PUBLIC_ID_KEY = "topic_brief_generation_public_id"


@st.cache_resource
def _session_factory() -> sessionmaker[Session]:
    """Shared SQLAlchemy session factory for the Streamlit process."""
    return create_session_factory(create_db_engine())


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
            st.success("Topic brief generation started.")

    accepted: TopicStatement | None = st.session_state.get(SESSION_KEY)
    public_id: uuid.UUID | None = st.session_state.get(PUBLIC_ID_KEY)
    if accepted is not None:
        st.subheader("Accepted topic statement")
        st.write(accepted.text)
        if public_id is not None:
            st.caption(f"Reference id: `{public_id}`")
