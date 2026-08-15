"""Generate paper brief Streamlit page (enqueue briefs + progress)."""

from __future__ import annotations

import os
from typing import Any, Mapping
from uuid import UUID

import streamlit as st
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.flows.serve import CREATE_PAPER_BRIEF_DEPLOYMENT_REF
from paper_reviewer.models.paper import get_paper_by_id
from paper_reviewer.models.paper_brief import get_paper_brief_by_paper_id
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_brief_generation.generate_paper_brief import (
    GeneratePaperBriefsEnqueueResult,
)
from paper_reviewer.schemas.topic_brief_generation.paper_archiving import (
    PaperArchivingResult,
)
from paper_reviewer.schemas.topic_brief_generation.topic_intake import TopicStatement
from paper_reviewer.topic_brief_generation.generate_paper_brief import (
    enqueue_generate_paper_briefs,
)
from paper_reviewer.ui.fulfill_papers_metadata import (
    may_submit_regenerate_paper,
    prefect_enqueue_error_hint,
    render_regenerate_button,
)
from paper_reviewer.ui.topic_scope_url import (
    parse_topic_scope_key,
    workflow_page_link,
)
from paper_reviewer.ui.new_topic_brief import (
    ARCHIVING_RESULT_KEY,
    GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY,
    SESSION_KEY,
)


@st.cache_resource
def _session_factory() -> sessionmaker[Session]:
    """Shared SQLAlchemy session factory for the Streamlit process."""
    return create_session_factory(create_db_engine())


def brief_prerequisites_met(
    state: Mapping[str, Any],
    *,
    topic_scope_key: UUID | None,
) -> bool:
    """Return True when archiving result is in session and generation key is in the URL."""
    return state.get(ARCHIVING_RESULT_KEY) is not None and topic_scope_key is not None


def brief_progress_label(
    *,
    full_text_status: PaperAspectStatus,
    brief_status: PaperAspectStatus | None,
    skipped_already_succeeded: bool,
) -> str:
    """Map full-text gate and brief status to a progress display label."""
    if full_text_status is PaperAspectStatus.not_started:
        return "Incomplete (fulfill papers metadata first)"
    if full_text_status in {
        PaperAspectStatus.failed,
        PaperAspectStatus.unavailable,
    }:
        return "Blocked (no full text)"
    if brief_status is PaperAspectStatus.succeeded:
        if skipped_already_succeeded:
            return "Skipped (already done)"
        return "Succeeded"
    if brief_status is PaperAspectStatus.failed:
        return "Failed"
    return "Fulfilling"


def _default_submit_brief(paper_id: int, doi: str) -> None:
    """Submit one create_paper_brief job (Prefect wiring in Compose)."""
    from paper_reviewer.flows.submit import submit_create_paper_brief

    submit_create_paper_brief(paper_id, doi)


def _paper_ids(archiving: PaperArchivingResult) -> list[int]:
    return [paper.id for paper in archiving.papers]


@st.fragment(run_every=2)
def _render_progress(
    paper_ids: list[int],
    enqueue_result: GeneratePaperBriefsEnqueueResult,
    *,
    topic_scope_key: UUID,
) -> None:
    skipped_terminal = set(enqueue_result.skipped_already_terminal)
    any_eligible_in_progress = False
    eligible_count = 0
    eligible_all_succeeded = True
    any_incomplete_fulfill = False

    with session_scope(_session_factory()) as session:
        rows: list[dict[str, Any]] = []
        for paper_id in paper_ids:
            paper = get_paper_by_id(session, paper_id)
            if paper is None:
                continue
            brief = get_paper_brief_by_paper_id(session, paper_id)
            brief_status = brief.status if brief is not None else None
            if paper.full_text_status is PaperAspectStatus.not_started:
                any_incomplete_fulfill = True
            if paper.full_text_status is PaperAspectStatus.succeeded:
                eligible_count += 1
                if brief_status is PaperAspectStatus.not_started or brief_status is None:
                    any_eligible_in_progress = True
                if brief_status is not PaperAspectStatus.succeeded:
                    eligible_all_succeeded = False
            label = brief_progress_label(
                full_text_status=paper.full_text_status,
                brief_status=brief_status,
                skipped_already_succeeded=(
                    paper_id in skipped_terminal
                    and brief_status is PaperAspectStatus.succeeded
                ),
            )
            error = None
            if (
                brief is not None
                and brief.status is PaperAspectStatus.failed
                and brief.error_message
            ):
                error = brief.error_message
            rows.append(
                {
                    "paper_id": paper_id,
                    "title": paper.title,
                    "url": paper.url,
                    "doi": paper.doi,
                    "source_status": paper.source_record_status,
                    "full_text_status": paper.full_text_status,
                    "label": label,
                    "error": error,
                }
            )

    st.subheader("Progress")
    if not rows:
        st.caption("No archived papers.")
        return

    if any_incomplete_fulfill:
        st.info(
            "Some papers still need Fulfill papers metadata. "
            "Briefs are enqueued only when full text is Succeeded."
        )
        workflow_page_link(
            "fulfill_papers_metadata",
            label="Go to Fulfill papers metadata",
            topic_scope_key=topic_scope_key,
        )

    for row in rows:
        st.markdown(f"**[{row['title']}]({row['url']})**")
        error_part = f" — {row['error']}" if row["error"] else ""
        st.caption(f"DOI `{row['doi']}` · brief {row['label']}{error_part}")
        if may_submit_regenerate_paper(
            row["source_status"],
            row["full_text_status"],
        ):
            render_regenerate_button(
                row["paper_id"],
                row["doi"],
                key_prefix="regenerate-brief",
            )

    eligible_terminal = not any_eligible_in_progress
    if eligible_terminal:
        if eligible_count == 0:
            st.info(
                "No papers in this set have full text Succeeded. "
                "Generate paper brief has nothing to enqueue."
            )
        elif eligible_all_succeeded:
            st.success("Generate paper brief finished for eligible papers.")
        else:
            st.info(
                "Generate paper brief finished for eligible papers. "
                "Some briefs failed."
            )
        st.caption("Next: Topic brief.")


def render_generate_paper_brief() -> None:
    """Render the Generate paper brief progress page."""
    st.title("Generate paper brief")

    topic_scope_key = parse_topic_scope_key(st.query_params)
    if not brief_prerequisites_met(st.session_state, topic_scope_key=topic_scope_key):
        st.info(
            "Archive papers and fulfill metadata before generating paper briefs. "
            "Open New Topic brief to start a generation, then archive papers."
        )
        workflow_page_link(
            "new_topic_brief",
            label="Go to New Topic brief",
            topic_scope_key=topic_scope_key,
        )
        workflow_page_link(
            "paper_archiving",
            label="Go to Paper archiving",
            topic_scope_key=topic_scope_key,
        )
        workflow_page_link(
            "fulfill_papers_metadata",
            label="Go to Fulfill papers metadata",
            topic_scope_key=topic_scope_key,
        )
        return

    assert topic_scope_key is not None
    archiving: PaperArchivingResult = st.session_state[ARCHIVING_RESULT_KEY]
    topic: TopicStatement | None = st.session_state.get(SESSION_KEY)
    paper_ids = _paper_ids(archiving)

    st.caption(f"Reference id: `{topic_scope_key}`")
    if topic is not None:
        snippet = topic.text if len(topic.text) <= 200 else f"{topic.text[:197]}..."
        st.write(snippet)

    if not paper_ids:
        st.caption("No archived papers.")
        st.success("Generate paper brief finished for this set.")
        st.caption("Next: Topic brief.")
        return

    enqueue_result: GeneratePaperBriefsEnqueueResult | None = st.session_state.get(
        GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY
    )
    if enqueue_result is None:
        try:
            with session_scope(_session_factory()) as session:
                enqueue_result = enqueue_generate_paper_briefs(
                    session,
                    paper_ids,
                    submit_brief=_default_submit_brief,
                )
        except Exception as exc:
            st.error(
                "Could not enqueue generate paper brief. "
                "Check Prefect configuration and try again."
            )
            st.caption(
                prefect_enqueue_error_hint(
                    os.environ.get("PREFECT_API_URL"),
                    CREATE_PAPER_BRIEF_DEPLOYMENT_REF,
                )
            )
            st.exception(exc)
            return
        st.session_state[GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY] = enqueue_result

    _render_progress(paper_ids, enqueue_result, topic_scope_key=topic_scope_key)
