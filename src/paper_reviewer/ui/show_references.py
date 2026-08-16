"""Show references Streamlit page (list Papers linked to the Topic scope)."""

from __future__ import annotations

from uuid import UUID

import streamlit as st
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.models.topic_brief_generation import get_topic_scope_by_key
from paper_reviewer.schemas.topic_brief_generation.show_references import (
    ReferencedPaper,
)
from paper_reviewer.topic_brief_generation.show_references import (
    list_show_references,
)
from paper_reviewer.ui.references_selection import (
    render_references_selection_header,
)
from paper_reviewer.ui.topic_scope_url import (
    parse_topic_scope_key,
    workflow_page_link,
)

MISSING_SCOPE_MESSAGE = (
    "Open Topic intake to create a Topic scope, then open Show references "
    "from References selection."
)
EMPTY_REFERENCES_CAPTION = "This Topic scope has no References yet."
LOAD_ERROR_MESSAGE = "Could not load References for this Topic scope. Try again."
PAPER_BRIEF_AVAILABLE_BADGE = "Paper brief available"
PAPER_BRIEF_NOT_AVAILABLE_BADGE = "Paper brief not available"
GO_TO_TOPIC_INTAKE_LABEL = "Go to Topic intake"
GO_TO_TOPIC_SCOPE_LABEL = "Go to Topic scope"
CONTINUE_TO_ADD_REFERENCE_LABEL = "Continue to Add reference"
GO_TO_REFERENCES_SELECTION_LABEL = "Go to References selection"


@st.cache_resource
def _session_factory() -> sessionmaker[Session]:
    """Shared SQLAlchemy session factory for the Streamlit process."""
    return create_session_factory(create_db_engine())


def format_referenced_paper_caption(paper: ReferencedPaper) -> str:
    """Caption line for one Reference bibliographic card."""
    authors = ", ".join(paper.authors) if paper.authors else "—"
    journal = paper.journal or "—"
    year = str(paper.published_year) if paper.published_year is not None else "—"
    return f"{authors} · {journal} · {year} · DOI `{paper.doi}`"


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


def _render_referenced_paper(paper: ReferencedPaper) -> None:
    st.markdown(f"**[{paper.title}]({paper.url})**")
    st.caption(format_referenced_paper_caption(paper))
    badge = (
        PAPER_BRIEF_AVAILABLE_BADGE
        if paper.paper_brief_available
        else PAPER_BRIEF_NOT_AVAILABLE_BADGE
    )
    st.badge(badge)

def _render_navigation(*, topic_scope_key: UUID) -> None:
    workflow_page_link(
        "add_reference",
        label=CONTINUE_TO_ADD_REFERENCE_LABEL,
        topic_scope_key=topic_scope_key,
    )
    workflow_page_link(
        "topic_scope",
        label=GO_TO_TOPIC_SCOPE_LABEL,
        topic_scope_key=topic_scope_key,
    )
    workflow_page_link(
        "references_selection",
        label=GO_TO_REFERENCES_SELECTION_LABEL,
        topic_scope_key=topic_scope_key,
    )


def render_show_references() -> None:
    """Render Show references for the Topic scope in the URL."""
    topic_scope_key = parse_topic_scope_key(st.query_params)
    render_references_selection_header(
        current_page_key="show_references",
        topic_scope_key=topic_scope_key,
    )
    st.header("Show references")

    if topic_scope_key is None:
        _render_missing_scope(topic_scope_key=None)
        return

    try:
        with session_scope(_session_factory()) as session:
            topic_scope = get_topic_scope_by_key(session, topic_scope_key)
            if topic_scope is None:
                _render_missing_scope(topic_scope_key=topic_scope_key)
                return
            result = list_show_references(session, topic_scope)
            papers = list(result.papers)
    except Exception:
        st.error(LOAD_ERROR_MESSAGE)
        return

    if not papers:
        st.caption(EMPTY_REFERENCES_CAPTION)
        _render_navigation(topic_scope_key=topic_scope_key)
        return

    for paper in papers:
        _render_referenced_paper(paper)
    _render_navigation(topic_scope_key=topic_scope_key)
