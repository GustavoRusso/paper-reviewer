"""Paper archiving Streamlit page (create-or-reuse Paper from triage retained)."""

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
from paper_reviewer.schemas.topic_brief_generation.retrieval_triage import (
    RetrievalTriageResult,
)
from paper_reviewer.schemas.topic_brief_generation.topic_intake import TopicStatement
from paper_reviewer.topic_brief_generation.paper_archiving import archive_papers
from paper_reviewer.ui.topic_scope_url import (
    parse_topic_scope_public_id,
    workflow_page_link,
)
from paper_reviewer.ui.new_topic_brief import (
    ARCHIVING_RESULT_KEY,
    FULFILL_ENQUEUE_RESULT_KEY,
    GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY,
    SESSION_KEY,
    TRIAGE_RESULT_KEY,
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


def archiving_prerequisites_met(state: Mapping[str, Any]) -> bool:
    """Return True when a confirmed retrieval triage result is in session state."""
    return state.get(TRIAGE_RESULT_KEY) is not None


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
    public_id: UUID | None,
) -> None:
    st.subheader("Summary")
    if public_id is not None:
        st.caption(f"Reference id: `{public_id}`")
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
            public_id=public_id,
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
        public_id=public_id,
    )


def render_paper_archiving() -> None:
    """Render the Paper archiving page."""
    st.title("Paper archiving")

    public_id = parse_topic_scope_public_id(st.query_params)
    if not archiving_prerequisites_met(st.session_state):
        st.info(
            "Confirm candidates on Retrieval triage before paper archiving. "
            "Open New Topic brief to start a generation, then confirm triage."
        )
        workflow_page_link(
            "new_topic_brief",
            label="Go to New Topic brief",
            public_id=public_id,
        )
        workflow_page_link(
            "retrieval_triage",
            label="Go to Retrieval triage",
            public_id=public_id,
        )
        return

    triage_result: RetrievalTriageResult = st.session_state[TRIAGE_RESULT_KEY]
    retained = triage_result.retained
    topic: TopicStatement | None = st.session_state.get(SESSION_KEY)

    if public_id is not None:
        st.caption(f"Reference id: `{public_id}`")
    if topic is not None:
        snippet = topic.text if len(topic.text) <= 200 else f"{topic.text[:197]}..."
        st.write(snippet)

    cached: PaperArchivingResult | None = st.session_state.get(ARCHIVING_RESULT_KEY)
    if cached is not None:
        _render_result(cached, input_count=len(retained), public_id=public_id)
        return

    try:
        with st.spinner("Archiving papers…"):
            with session_scope(_session_factory()) as session:
                archiving_result = archive_papers(session, retained)
    except Exception:
        st.error("Paper archiving failed. Try again from Retrieval triage.")
        return

    st.session_state[ARCHIVING_RESULT_KEY] = archiving_result
    st.session_state.pop(FULFILL_ENQUEUE_RESULT_KEY, None)
    st.session_state.pop(GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY, None)
    _render_result(
        archiving_result,
        input_count=len(retained),
        public_id=public_id,
    )
