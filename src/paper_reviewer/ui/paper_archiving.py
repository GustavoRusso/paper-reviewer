"""Paper archiving Streamlit page (create-or-reuse Paper from search candidates)."""

from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

import streamlit as st
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.schemas.topic_brief_generation.paper_archiving import (
    ArchiveSkip,
    ArchiveSkipReason,
    Paper,
    PaperArchivingResult,
)
from paper_reviewer.schemas.topic_brief_generation.related_paper_search import (
    RelatedPaperSearchResult,
)
from paper_reviewer.schemas.topic_brief_generation.topic_intake import TopicStatement
from paper_reviewer.topic_brief_generation.paper_archiving import archive_papers
from paper_reviewer.ui.paper_ingestion import render_paper_ingestion_header
from paper_reviewer.ui.related_paper_search import search_cache_matches
from paper_reviewer.ui.topic_scope_url import (
    parse_topic_scope_key,
    workflow_page_link,
)
from paper_reviewer.ui.topic_intake import (
    ARCHIVING_RESULT_KEY,
    FULFILL_ENQUEUE_RESULT_KEY,
    GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY,
    SEARCH_KEY,
    SESSION_KEY,
)

_SKIP_REASON_LABELS: dict[ArchiveSkipReason, str] = {
    ArchiveSkipReason.missing_doi: "Missing DOI",
    ArchiveSkipReason.invalid_required_field: "Invalid required field",
    ArchiveSkipReason.doi_conflict: "DOI conflict",
}


@st.cache_resource
def _session_factory() -> sessionmaker[Session]:
    """Shared SQLAlchemy session factory for the Streamlit process."""
    return create_session_factory(create_db_engine())


def archiving_prerequisites_met(
    state: Mapping[str, Any],
    *,
    topic_scope_key: UUID | None,
) -> bool:
    """Return True when related-paper search cache matches the URL Topic scope."""
    return search_cache_matches(state, topic_scope_key=topic_scope_key)


def archive_skip_reason_label(reason: ArchiveSkipReason) -> str:
    """Human-readable label for an archive skip reason."""
    return _SKIP_REASON_LABELS[reason]


def format_archived_paper_caption(paper: Paper) -> str:
    """Caption line for one archived Paper card."""
    authors = ", ".join(paper.authors) if paper.authors else "—"
    journal = paper.journal or "—"
    year = str(paper.published_year) if paper.published_year is not None else "—"
    created = paper.created_at.isoformat()
    return (
        f"{authors} · {journal} · {year} · DOI `{paper.doi}` · "
        f"`{paper.source_id}` / `{paper.source_uid}` · {created}"
    )


def format_paper_archiving_summary(result: PaperArchivingResult) -> str:
    """Short summary line for archive counts."""
    return (
        f"Paper archiving finished: {len(result.papers)} paper(s), "
        f"{len(result.skipped)} skipped, {len(result.errors)} error(s)."
    )


def _render_archived_paper(paper: Paper) -> None:
    st.markdown(f"**[{paper.title}]({paper.url})**")
    st.caption(format_archived_paper_caption(paper))


def _render_skip(item: ArchiveSkip) -> None:
    identity = (
        f"`{item.source_id}` / `{item.source_uid}`"
        if item.source_id is not None and item.source_uid is not None
        else "—"
    )
    doi_part = f" · DOI `{item.doi}`" if item.doi else ""
    st.write(
        f"{identity}{doi_part} — {archive_skip_reason_label(item.reason)}"
    )


def _render_result(
    result: PaperArchivingResult,
    *,
    input_count: int,
    topic_scope_key: UUID | None,
) -> None:
    st.subheader("Summary")
    if topic_scope_key is not None:
        st.caption(f"Reference id: `{topic_scope_key}`")
    st.write(
        f"Input candidates: {input_count}. "
        f"Archived: {len(result.papers)}. "
        f"Skipped: {len(result.skipped)}. "
        f"Errors: {len(result.errors)}."
    )
    st.caption(format_paper_archiving_summary(result))

    if (
        input_count == 0
        and not result.papers
        and not result.skipped
        and not result.errors
    ):
        st.caption("No candidates to archive")
        workflow_page_link(
            "fulfill_papers_metadata",
            label="Continue to Fulfill papers metadata",
            topic_scope_key=topic_scope_key,
        )
        return

    st.subheader("Archived papers")
    if not result.papers:
        st.caption("No papers archived.")
    else:
        for paper in result.papers:
            _render_archived_paper(paper)

    st.subheader("Skipped")
    if not result.skipped:
        st.caption("No skipped candidates.")
    else:
        for item in result.skipped:
            _render_skip(item)

    st.subheader("Errors")
    if not result.errors:
        st.caption("No errors.")
    else:
        for err in result.errors:
            identity = (
                f"`{err.source_id}` / `{err.source_uid}`"
                if err.source_id is not None and err.source_uid is not None
                else "—"
            )
            doi_part = f" · DOI `{err.doi}`" if err.doi else ""
            st.error(f"{identity}{doi_part} — {err.reason}")

    workflow_page_link(
        "fulfill_papers_metadata",
        label="Continue to Fulfill papers metadata",
        topic_scope_key=topic_scope_key,
    )


def render_paper_archiving() -> None:
    """Render the Paper archiving page."""
    topic_scope_key = parse_topic_scope_key(st.query_params)
    render_paper_ingestion_header(
        current_page_key="paper_archiving",
        topic_scope_key=topic_scope_key,
    )
    st.title("Paper archiving")

    if not archiving_prerequisites_met(
        st.session_state,
        topic_scope_key=topic_scope_key,
    ):
        st.info(
            "Run related-paper search before paper archiving. "
            "Open Topic intake to start a Topic scope, then search paper sources."
        )
        workflow_page_link(
            "topic_intake",
            label="Go to Topic intake",
            topic_scope_key=topic_scope_key,
        )
        workflow_page_link(
            "topic_scope",
            label="Go to Topic scope",
            topic_scope_key=topic_scope_key,
        )
        workflow_page_link(
            "related_paper_search",
            label="Go to Related-paper search",
            topic_scope_key=topic_scope_key,
        )
        return

    search_result: RelatedPaperSearchResult = st.session_state[SEARCH_KEY]
    candidates = search_result.candidates
    topic: TopicStatement | None = st.session_state.get(SESSION_KEY)

    if topic_scope_key is not None:
        st.caption(f"Reference id: `{topic_scope_key}`")
    if topic is not None:
        snippet = topic.text if len(topic.text) <= 200 else f"{topic.text[:197]}..."
        st.write(snippet)

    cached: PaperArchivingResult | None = st.session_state.get(ARCHIVING_RESULT_KEY)
    if cached is not None:
        _render_result(
            cached,
            input_count=len(candidates),
            topic_scope_key=topic_scope_key,
        )
        return

    try:
        with st.spinner("Archiving papers…"):
            with session_scope(_session_factory()) as session:
                archiving_result = archive_papers(session, candidates)
    except Exception:
        st.error("Paper archiving failed. Try again from Related-paper search.")
        return

    st.session_state[ARCHIVING_RESULT_KEY] = archiving_result
    st.session_state.pop(FULFILL_ENQUEUE_RESULT_KEY, None)
    st.session_state.pop(GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY, None)
    _render_result(
        archiving_result,
        input_count=len(candidates),
        topic_scope_key=topic_scope_key,
    )
