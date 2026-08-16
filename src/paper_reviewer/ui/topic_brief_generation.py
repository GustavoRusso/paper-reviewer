"""Topic brief generation phase landing Streamlit page."""

from __future__ import annotations

import os
from uuid import UUID

import streamlit as st
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.flows.serve import CREATE_TOPIC_BRIEF_DEPLOYMENT_REF
from paper_reviewer.models.topic_scope import get_topic_scope_by_key
from paper_reviewer.models.topic_scope.topic_brief import (
    get_topic_brief_by_topic_scope_id,
)
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.topic_scope.topic_brief_generation import (
    count_briefed_references,
    enqueue_create_topic_brief,
)
from paper_reviewer.ui.fulfill_papers_metadata import prefect_enqueue_error_hint
from paper_reviewer.ui.topic_scope_url import (
    parse_topic_scope_key,
    workflow_page_link,
)

MISSING_SCOPE_MESSAGE = (
    "Open Topic intake to create a Topic scope, then open Topic brief "
    "generation from the Topic scope hub."
)
ZERO_BRIEFED_CAPTION = (
    "Generation needs at least one Reference with a succeeded paper brief."
)
LOAD_ERROR_MESSAGE = (
    "Could not load Topic brief generation for this Topic scope. Try again."
)
ENQUEUE_ERROR_MESSAGE = (
    "Could not enqueue topic brief generation. "
    "Check Prefect configuration and try again."
)
GENERATING_STATUS_LABEL = "Generating topic brief…"
SUCCEEDED_STATUS_LABEL = "Topic brief ready"
GENERATE_TOPIC_BRIEF_LABEL = "Generate topic brief"
GO_TO_TOPIC_INTAKE_LABEL = "Go to Topic intake"
GO_TO_TOPIC_SCOPE_LABEL = "Go to Topic scope"
GO_TO_SHOW_REFERENCES_LABEL = "Go to Show references"
GO_TO_GENERATE_PAPER_BRIEF_LABEL = "Go to Generate paper brief"


def generate_button_enabled(
    *,
    briefed_count: int,
    status: PaperAspectStatus | None,
) -> bool:
    """Return True when Generate may be clicked (not zero-briefed, not in flight)."""
    if briefed_count <= 0:
        return False
    if status is PaperAspectStatus.not_started:
        return False
    return True


def is_in_flight(status: PaperAspectStatus | None) -> bool:
    """Return True when a TopicBrief row is waiting for create_topic_brief."""
    return status is PaperAspectStatus.not_started


@st.cache_resource
def _session_factory() -> sessionmaker[Session]:
    """Shared SQLAlchemy session factory for the Streamlit process."""
    return create_session_factory(create_db_engine())


def _default_submit(topic_scope_id: int) -> None:
    from paper_reviewer.flows.submit import submit_create_topic_brief

    submit_create_topic_brief(topic_scope_id)


def _render_missing_scope(*, topic_scope_key: UUID | None) -> None:
    st.info(MISSING_SCOPE_MESSAGE)
    workflow_page_link(
        "topic_intake",
        label=GO_TO_TOPIC_INTAKE_LABEL,
        topic_scope_key=topic_scope_key,
    )
    workflow_page_link(
        "topic_scope",
        label=GO_TO_TOPIC_SCOPE_LABEL,
        topic_scope_key=topic_scope_key,
    )


def _render_navigation(
    *,
    topic_scope_key: UUID,
    show_zero_briefed_links: bool,
) -> None:
    workflow_page_link(
        "topic_scope",
        label=GO_TO_TOPIC_SCOPE_LABEL,
        topic_scope_key=topic_scope_key,
    )
    if show_zero_briefed_links:
        workflow_page_link(
            "show_references",
            label=GO_TO_SHOW_REFERENCES_LABEL,
            topic_scope_key=topic_scope_key,
        )
        workflow_page_link(
            "generate_paper_brief",
            label=GO_TO_GENERATE_PAPER_BRIEF_LABEL,
            topic_scope_key=topic_scope_key,
        )


@st.fragment(run_every=2)
def _render_progress(*, topic_scope_id: int) -> None:
    with session_scope(_session_factory()) as session:
        brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
        status = brief.status if brief is not None else None
        error_message = brief.error_message if brief is not None else None
        has_content = brief is not None and brief.content is not None

    if status is PaperAspectStatus.not_started:
        with st.status(GENERATING_STATUS_LABEL, expanded=True, state="running"):
            st.write("Drafting from briefed References…")
        return

    if status is PaperAspectStatus.succeeded:
        with st.status(SUCCEEDED_STATUS_LABEL, state="complete"):
            st.write("Topic brief generated.")
        return

    if status is PaperAspectStatus.failed:
        st.error(error_message or "Topic brief generation failed.")
        if has_content:
            st.caption("Showing the last successful topic brief content.")
        return


def render_topic_brief_generation() -> None:
    """Render the Topic brief generation landing for the Topic scope in the URL."""
    st.title("Topic brief generation")
    topic_scope_key = parse_topic_scope_key(st.query_params)
    if topic_scope_key is None:
        _render_missing_scope(topic_scope_key=None)
        return

    st.caption(f"Reference id: `{topic_scope_key}`")

    try:
        with session_scope(_session_factory()) as session:
            topic_scope = get_topic_scope_by_key(session, topic_scope_key)
            if topic_scope is None:
                _render_missing_scope(topic_scope_key=topic_scope_key)
                return
            topic_scope_id = topic_scope.id
            briefed_count = count_briefed_references(session, topic_scope_id)
            brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
            status = brief.status if brief is not None else None
    except Exception:
        st.error(LOAD_ERROR_MESSAGE)
        return

    zero_briefed = briefed_count == 0
    if zero_briefed:
        st.caption(ZERO_BRIEFED_CAPTION)

    if status is not None:
        _render_progress(topic_scope_id=topic_scope_id)

    if st.button(
        GENERATE_TOPIC_BRIEF_LABEL,
        type="primary",
        disabled=not generate_button_enabled(
            briefed_count=briefed_count,
            status=status,
        ),
    ):
        try:
            with session_scope(_session_factory()) as session:
                enqueue_create_topic_brief(
                    session,
                    topic_scope_id,
                    submit=_default_submit,
                )
        except Exception as exc:
            st.error(ENQUEUE_ERROR_MESSAGE)
            st.caption(
                prefect_enqueue_error_hint(
                    os.environ.get("PREFECT_API_URL"),
                    CREATE_TOPIC_BRIEF_DEPLOYMENT_REF,
                )
            )
            st.exception(exc)
            return
        st.rerun()

    _render_navigation(
        topic_scope_key=topic_scope_key,
        show_zero_briefed_links=zero_briefed,
    )
