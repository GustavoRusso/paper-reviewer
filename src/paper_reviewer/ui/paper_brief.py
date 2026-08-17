"""Paper brief Streamlit page (read a succeeded global PaperBrief by DOI)."""

from __future__ import annotations

from uuid import UUID

import streamlit as st
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    PaperBriefContent,
)
from paper_reviewer.schemas.topic_scope.paper_brief import (
    PaperBriefRead,
    PaperBriefReadStatus,
)
from paper_reviewer.topic_scope.paper_brief import (
    load_paper_brief_for_read,
)
from paper_reviewer.ui.topic_scope_url import (
    parse_doi,
    parse_topic_scope_key,
    workflow_page_link,
)

MISSING_DOI_MESSAGE = (
    "Open this page from Show references to read a paper brief."
)
PAPER_MISSING_MESSAGE = "No ingested paper matches this DOI."
NO_SUCCEEDED_BRIEF_MESSAGE = "This paper has no succeeded paper brief yet."
INVALID_CONTENT_MESSAGE = "Stored paper brief content could not be displayed."
LOAD_ERROR_MESSAGE = "Could not load the paper brief. Try again."
GO_TO_SHOW_REFERENCES_LABEL = "Go to Show references"

_OPTIONAL_BEFORE_FINDINGS: tuple[tuple[str, str], ...] = (
    ("study_type", "Study type"),
    ("timeline_geography", "Timeline and geography"),
    ("population_sample", "Population and sample"),
    ("key_methods", "Key methods"),
)
_OPTIONAL_AFTER_FINDINGS: tuple[tuple[str, str], ...] = (
    ("discussion", "Discussion"),
    ("limitations", "Limitations"),
    ("recommendations", "Recommendations"),
)


@st.cache_resource
def _session_factory() -> sessionmaker[Session]:
    """Shared SQLAlchemy session factory for the Streamlit process."""
    return create_session_factory(create_db_engine())


def format_paper_brief_caption(
    *,
    authors: list[str],
    journal: str | None,
    published_year: int | None,
    doi: str,
) -> str:
    """Caption line for the Paper brief bibliographic header."""
    authors_text = ", ".join(authors) if authors else "—"
    journal_text = journal or "—"
    year = str(published_year) if published_year is not None else "—"
    return f"{authors_text} · {journal_text} · {year} · DOI `{doi}`"


def paper_brief_display_sections(
    content: PaperBriefContent,
) -> list[tuple[str, str | list[str]]]:
    """Return labeled sections in template order, skipping empty optionals."""
    sections: list[tuple[str, str | list[str]]] = [
        ("Summary", content.summary),
        ("Objective", content.objective),
    ]
    for field_name, label in _OPTIONAL_BEFORE_FINDINGS:
        value = getattr(content, field_name)
        if value:
            sections.append((label, value))
    sections.append(("Key findings", content.key_findings))
    for field_name, label in _OPTIONAL_AFTER_FINDINGS:
        value = getattr(content, field_name)
        if value:
            sections.append((label, value))
    return sections


def _render_show_references_link(*, topic_scope_key: UUID | None) -> None:
    if topic_scope_key is None:
        return
    workflow_page_link(
        "show_references",
        label=GO_TO_SHOW_REFERENCES_LABEL,
        topic_scope_key=topic_scope_key,
    )


def _render_header(result: PaperBriefRead) -> None:
    if result.title and result.url:
        st.markdown(f"**[{result.title}]({result.url})**")
    elif result.title:
        st.markdown(f"**{result.title}**")
    st.caption(
        format_paper_brief_caption(
            authors=result.authors,
            journal=result.journal,
            published_year=result.published_year,
            doi=result.doi,
        )
    )


def _render_content(content: PaperBriefContent) -> None:
    for label, value in paper_brief_display_sections(content):
        st.subheader(label)
        if isinstance(value, list):
            for item in value:
                st.markdown(f"- {item}")
        else:
            st.write(value)


def render_paper_brief() -> None:
    """Render the Paper brief reader for the DOI in the URL."""
    st.title("Paper brief")
    doi = parse_doi(st.query_params)
    topic_scope_key = parse_topic_scope_key(st.query_params)

    if doi is None:
        st.caption(MISSING_DOI_MESSAGE)
        _render_show_references_link(topic_scope_key=topic_scope_key)
        return

    try:
        with session_scope(_session_factory()) as session:
            result = load_paper_brief_for_read(session, doi)
    except Exception:
        st.error(LOAD_ERROR_MESSAGE)
        _render_show_references_link(topic_scope_key=topic_scope_key)
        return

    if result.status is PaperBriefReadStatus.paper_missing:
        st.caption(PAPER_MISSING_MESSAGE)
        _render_show_references_link(topic_scope_key=topic_scope_key)
        return

    if result.status is PaperBriefReadStatus.brief_unavailable:
        _render_header(result)
        st.caption(NO_SUCCEEDED_BRIEF_MESSAGE)
        _render_show_references_link(topic_scope_key=topic_scope_key)
        return

    _render_header(result)
    if result.status is PaperBriefReadStatus.invalid_content or result.content is None:
        st.warning(INVALID_CONTENT_MESSAGE)
        _render_show_references_link(topic_scope_key=topic_scope_key)
        return

    _render_content(result.content)
    _render_show_references_link(topic_scope_key=topic_scope_key)
