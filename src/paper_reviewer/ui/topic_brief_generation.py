"""Topic brief generation phase landing Streamlit page."""

from __future__ import annotations

import os
from typing import Any
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
from paper_reviewer.schemas.topic_scope.topic_brief_generation import (
    TopicBriefContent,
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
LAST_GOOD_CONTENT_CAPTION = "Showing the last successful topic brief content."
GENERATING_STATUS_LABEL = "Generating topic brief…"
SUCCEEDED_STATUS_LABEL = "Topic brief ready"
GENERATE_TOPIC_BRIEF_LABEL = "Generate topic brief"
REGENERATE_TOPIC_BRIEF_LABEL = "Regenerate topic brief"
GO_TO_TOPIC_INTAKE_LABEL = "Go to Topic intake"
GO_TO_TOPIC_SCOPE_LABEL = "Go to Topic scope"
GO_TO_SHOW_REFERENCES_LABEL = "Go to Show references"
GO_TO_GENERATE_PAPER_BRIEF_LABEL = "Go to Generate paper brief"

_ASSISTANT_OUTPUT_HEADING = "Assistant output:"


def generate_button_enabled(
    *,
    briefed_count: int,
    status: PaperAspectStatus | None,
) -> bool:
    """Return True when Generate/Regenerate may be clicked."""
    if briefed_count <= 0:
        return False
    if status is PaperAspectStatus.not_started:
        return False
    return True


def generate_button_label(*, has_content: bool) -> str:
    """Return Generate or Regenerate based on stored topic brief content."""
    if has_content:
        return REGENERATE_TOPIC_BRIEF_LABEL
    return GENERATE_TOPIC_BRIEF_LABEL


def is_in_flight(status: PaperAspectStatus | None) -> bool:
    """Return True when a TopicBrief row is waiting for create_topic_brief."""
    return status is PaperAspectStatus.not_started


def should_render_topic_brief_content(
    *,
    status: PaperAspectStatus | None,
    has_content: bool,
) -> bool:
    """Return True when stored content should be shown as the primary brief."""
    if not has_content:
        return False
    return status in {
        PaperAspectStatus.succeeded,
        PaperAspectStatus.failed,
    }


def split_topic_brief_error_message(
    error_message: str,
) -> tuple[str, str | None]:
    """Split a stored topic-brief error into caption text and optional dump."""
    index = error_message.find(_ASSISTANT_OUTPUT_HEADING)
    if index < 0:
        return error_message, None
    caption = error_message[:index].rstrip()
    assistant = error_message[index + len(_ASSISTANT_OUTPUT_HEADING) :].lstrip("\n")
    if not assistant:
        return caption, None
    return caption, assistant


def doi_content_url(doi: str) -> str:
    """Return an external DOI resolver URL for a content link."""
    return f"https://doi.org/{doi}"


def parse_stored_topic_brief_content(
    content: dict[str, Any] | None,
) -> TopicBriefContent | None:
    """Validate stored JSONB content, or return None when missing/invalid."""
    if content is None:
        return None
    try:
        return TopicBriefContent.model_validate(content)
    except Exception:
        return None


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


def _render_topic_brief_content(content: TopicBriefContent) -> None:
    st.header(content.title)
    st.write(content.abstract)
    st.write(content.introduction)
    for section in content.sections:
        st.subheader(section.heading)
        st.write(section.body)
    st.write(content.concluding_section)
    if content.key_points:
        st.subheader("Key points")
        for point in content.key_points:
            st.markdown(f"- {point}")
    if content.citations:
        st.subheader("Citations")
        for citation in content.citations:
            doi = citation.doi.strip()
            if doi:
                st.markdown(
                    f"{citation.n}. [{citation.text}]({doi_content_url(doi)})"
                )
            else:
                st.markdown(f"{citation.n}. {citation.text}")


def _render_failed_error(error_message: str | None) -> None:
    raw = error_message or "Topic brief generation failed."
    caption, assistant = split_topic_brief_error_message(raw)
    st.error(caption)
    if assistant:
        with st.expander("Assistant output"):
            st.code(assistant)


@st.fragment(run_every=2)
def _render_body(
    *,
    topic_scope_id: int,
    topic_scope_key: UUID,
    briefed_count: int,
) -> None:
    with session_scope(_session_factory()) as session:
        brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
        status = brief.status if brief is not None else None
        error_message = brief.error_message if brief is not None else None
        raw_content = brief.content if brief is not None else None

    has_content = raw_content is not None
    content = parse_stored_topic_brief_content(raw_content)

    if status is PaperAspectStatus.not_started:
        with st.status(GENERATING_STATUS_LABEL, expanded=True, state="running"):
            st.write("Drafting from briefed References…")
    elif status is PaperAspectStatus.succeeded:
        with st.status(SUCCEEDED_STATUS_LABEL, state="complete"):
            st.write("Topic brief generated.")
    elif status is PaperAspectStatus.failed:
        _render_failed_error(error_message)
        if has_content:
            st.caption(LAST_GOOD_CONTENT_CAPTION)

    if should_render_topic_brief_content(status=status, has_content=has_content):
        if content is not None:
            _render_topic_brief_content(content)
        else:
            st.warning("Stored topic brief content could not be displayed.")

    if st.button(
        generate_button_label(has_content=has_content),
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
        show_zero_briefed_links=briefed_count == 0,
    )


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
    except Exception:
        st.error(LOAD_ERROR_MESSAGE)
        return

    if briefed_count == 0:
        st.caption(ZERO_BRIEFED_CAPTION)

    _render_body(
        topic_scope_id=topic_scope_id,
        topic_scope_key=topic_scope_key,
        briefed_count=briefed_count,
    )
