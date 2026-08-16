"""Add reference Streamlit page (Papers search results; attach not built)."""

from __future__ import annotations

from uuid import UUID

import streamlit as st
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.models.topic_brief_generation import (
    get_topic_scope_by_key,
    list_topic_facets_for_scope,
)
from paper_reviewer.schemas.topic_brief_generation.papers_search import (
    PaperSearchHit,
)
from paper_reviewer.topic_brief_generation.papers_search import search_papers
from paper_reviewer.ui.references_selection import (
    render_references_selection_header,
)
from paper_reviewer.ui.topic_scope_url import (
    parse_topic_scope_key,
    workflow_page_link,
)

MISSING_SCOPE_MESSAGE = (
    "Open Topic intake to create a Topic scope, then open Add reference "
    "from References selection."
)
EMPTY_NO_CONCEPTS_CAPTION = (
    "No topic facet concepts to search. Run Topic analysis first."
)
EMPTY_NO_HITS_CAPTION = (
    "No ingested papers match this Topic scope's concepts."
)
TRUNCATED_CAPTION = "Showing the first 20 matching papers."
LOAD_ERROR_MESSAGE = (
    "Could not load Papers search for this Topic scope. Try again."
)
ATTACH_NOT_BUILT_CAPTION = (
    "Attaching References from local search results is not built yet."
)
ALREADY_REFERENCED_BADGE = "Already a Reference"
NOT_YET_REFERENCED_BADGE = "Not yet a Reference"
GO_TO_TOPIC_INTAKE_LABEL = "Go to Topic intake"
GO_TO_TOPIC_SCOPE_LABEL = "Go to Topic scope"
GO_TO_SHOW_REFERENCES_LABEL = "Go to Show references"


@st.cache_resource
def _session_factory() -> sessionmaker[Session]:
    """Shared SQLAlchemy session factory for the Streamlit process."""
    return create_session_factory(create_db_engine())


def format_paper_search_hit_caption(hit: PaperSearchHit) -> str:
    """Caption line for one Papers search hit card."""
    authors = ", ".join(hit.authors) if hit.authors else "—"
    journal = hit.journal or "—"
    year = str(hit.published_year) if hit.published_year is not None else "—"
    return f"{authors} · {journal} · {year} · DOI `{hit.doi}`"


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


def _render_hit(hit: PaperSearchHit) -> None:
    st.markdown(f"**[{hit.title}]({hit.url})**")
    st.caption(format_paper_search_hit_caption(hit))
    badge = (
        ALREADY_REFERENCED_BADGE
        if hit.already_referenced
        else NOT_YET_REFERENCED_BADGE
    )
    st.badge(badge)


def _render_navigation(*, topic_scope_key: UUID) -> None:
    workflow_page_link(
        "show_references",
        label=GO_TO_SHOW_REFERENCES_LABEL,
        topic_scope_key=topic_scope_key,
    )


def _has_usable_concepts(session: Session, topic_scope_id: int) -> bool:
    for facet in list_topic_facets_for_scope(session, topic_scope_id):
        for raw in facet.concepts:
            if raw.strip():
                return True
    return False


def render_add_reference() -> None:
    """Render Add reference: Papers search results for the Topic scope."""
    topic_scope_key = parse_topic_scope_key(st.query_params)
    render_references_selection_header(
        current_page_key="add_reference",
        topic_scope_key=topic_scope_key,
    )
    st.header("Add reference")

    if topic_scope_key is None:
        _render_missing_scope(topic_scope_key=None)
        return

    try:
        with session_scope(_session_factory()) as session:
            topic_scope = get_topic_scope_by_key(session, topic_scope_key)
            if topic_scope is None:
                _render_missing_scope(topic_scope_key=topic_scope_key)
                return
            result = search_papers(session, topic_scope)
            hits = list(result.hits)
            truncated = result.truncated
            no_concepts = not hits and not truncated and not _has_usable_concepts(
                session, topic_scope.id
            )
    except Exception:
        st.error(LOAD_ERROR_MESSAGE)
        return

    if truncated:
        st.caption(TRUNCATED_CAPTION)

    if not hits:
        if no_concepts:
            st.caption(EMPTY_NO_CONCEPTS_CAPTION)
        else:
            st.caption(EMPTY_NO_HITS_CAPTION)
    else:
        for hit in hits:
            _render_hit(hit)

    st.caption(ATTACH_NOT_BUILT_CAPTION)
    _render_navigation(topic_scope_key=topic_scope_key)
