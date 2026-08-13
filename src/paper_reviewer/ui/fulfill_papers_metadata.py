"""Fulfill papers metadata Streamlit page (enqueue inform + progress)."""

from __future__ import annotations

import os
from typing import Any, Mapping
from uuid import UUID

import streamlit as st
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.flows.serve import INFORM_DEPLOYMENT_REF
from paper_reviewer.models.topic_brief_generation.paper import get_paper_by_id
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    FulfillPapersMetadataEnqueueResult,
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_brief_generation.paper_archiving import (
    PaperArchivingResult,
)
from paper_reviewer.schemas.topic_brief_generation.topic_intake import TopicStatement
from paper_reviewer.topic_brief_generation.fulfill_papers_metadata import (
    enqueue_fulfill_papers_metadata,
)
from paper_reviewer.ui.navigation import streamlit_page_for
from paper_reviewer.ui.topic_intake import (
    ARCHIVING_RESULT_KEY,
    FULFILL_ENQUEUE_RESULT_KEY,
    PUBLIC_ID_KEY,
    SESSION_KEY,
)


@st.cache_resource
def _session_factory() -> sessionmaker[Session]:
    """Shared SQLAlchemy session factory for the Streamlit process."""
    return create_session_factory(create_db_engine())


def fulfill_prerequisites_met(state: Mapping[str, Any]) -> bool:
    """Return True when archiving result and generation id are in session."""
    return (
        state.get(ARCHIVING_RESULT_KEY) is not None
        and state.get(PUBLIC_ID_KEY) is not None
    )


def aspect_status_label(
    *,
    status: PaperAspectStatus,
    skipped_already_succeeded: bool,
) -> str:
    """Map one stored aspect status to a progress display label."""
    if status is PaperAspectStatus.succeeded:
        if skipped_already_succeeded:
            return "Skipped (already done)"
        return "Succeeded"
    if status is PaperAspectStatus.failed:
        return "Failed"
    if status is PaperAspectStatus.unavailable:
        return "Unavailable"
    return "Fulfilling"


def enrichment_links_caption(
    pmc_article_url: str | None,
    open_access_pdf_url: str | None,
) -> str | None:
    """Build optional markdown for PMC / PDF links on the progress row."""
    parts: list[str] = []
    if pmc_article_url:
        parts.append(f"[PMC article]({pmc_article_url})")
    if open_access_pdf_url:
        parts.append(f"[Open access PDF]({open_access_pdf_url})")
    if not parts:
        return None
    return " · ".join(parts)


def prefect_enqueue_error_hint(
    prefect_api_url: str | None,
    deployment_ref: str,
) -> str:
    """Build operator hint when Prefect enqueue fails."""
    url_display = prefect_api_url if prefect_api_url else "(unset)"
    return (
        "The UI container must reach Prefect at "
        f"`PREFECT_API_URL={url_display}` and the "
        "`prefect-worker` service must serve deployment "
        f"`{deployment_ref}`."
    )


def _default_submit_inform(paper_id: int, doi: str) -> None:
    """Submit one inform job (Prefect wiring lands with Compose services)."""
    from paper_reviewer.flows.submit import submit_inform_paper_from_source

    submit_inform_paper_from_source(paper_id, doi)


def _paper_ids(archiving: PaperArchivingResult) -> list[int]:
    return [paper.id for paper in archiving.papers]


def _is_terminal(status: PaperAspectStatus) -> bool:
    return status is not PaperAspectStatus.not_started


def _aspect_error_text(
    *,
    source_record_status: PaperAspectStatus,
    source_record_error_message: str | None,
    full_text_status: PaperAspectStatus,
    full_text_error_message: str | None,
) -> str | None:
    parts: list[str] = []
    if (
        source_record_status is PaperAspectStatus.failed
        and source_record_error_message
    ):
        parts.append(source_record_error_message)
    if full_text_status is PaperAspectStatus.failed and full_text_error_message:
        parts.append(full_text_error_message)
    if not parts:
        return None
    return "; ".join(parts)


@st.fragment(run_every=2)
def _render_progress(
    paper_ids: list[int],
    enqueue_result: FulfillPapersMetadataEnqueueResult,
) -> None:
    skipped_informed = set(enqueue_result.skipped_already_informed)
    any_non_terminal = False
    all_succeeded = True

    with session_scope(_session_factory()) as session:
        rows: list[dict[str, Any]] = []
        for paper_id in paper_ids:
            paper = get_paper_by_id(session, paper_id)
            if paper is None:
                continue
            source_status = paper.source_record_status
            full_text_status = paper.full_text_status
            source_label = aspect_status_label(
                status=source_status,
                skipped_already_succeeded=(
                    paper_id in skipped_informed
                    and source_status is PaperAspectStatus.succeeded
                ),
            )
            full_text_label = aspect_status_label(
                status=full_text_status,
                skipped_already_succeeded=(
                    paper_id in skipped_informed
                    and full_text_status is PaperAspectStatus.succeeded
                ),
            )
            if not _is_terminal(source_status) or not _is_terminal(full_text_status):
                any_non_terminal = True
            if (
                source_status is not PaperAspectStatus.succeeded
                or full_text_status is not PaperAspectStatus.succeeded
            ):
                all_succeeded = False
            rows.append(
                {
                    "title": paper.title,
                    "url": paper.url,
                    "doi": paper.doi,
                    "source_label": source_label,
                    "full_text_label": full_text_label,
                    "error": _aspect_error_text(
                        source_record_status=source_status,
                        source_record_error_message=paper.source_record_error_message,
                        full_text_status=full_text_status,
                        full_text_error_message=paper.full_text_error_message,
                    ),
                    "pmc_article_url": paper.pmc_article_url,
                    "open_access_pdf_url": paper.open_access_pdf_url,
                }
            )

    st.subheader("Progress")
    if not rows:
        st.caption("No archived papers.")
        return

    for row in rows:
        st.markdown(f"**[{row['title']}]({row['url']})**")
        error_part = f" — {row['error']}" if row["error"] else ""
        st.caption(
            f"DOI `{row['doi']}` · source record {row['source_label']} · "
            f"full text {row['full_text_label']}{error_part}"
        )
        links = enrichment_links_caption(
            row["pmc_article_url"],
            row["open_access_pdf_url"],
        )
        if links:
            st.caption(links)

    all_terminal = not any_non_terminal
    if all_terminal:
        if all_succeeded:
            st.success("Fulfill papers metadata finished for this set.")
        else:
            st.info(
                "Fulfill papers metadata finished. Some papers failed or are "
                "unavailable; later steps use papers with full text Succeeded."
            )
        st.caption("Next: Generate paper brief.")


def render_fulfill_papers_metadata() -> None:
    """Render the Fulfill papers metadata progress page."""
    st.title("Fulfill papers metadata")

    if not fulfill_prerequisites_met(st.session_state):
        st.info(
            "Archive papers on Paper archiving before fulfilling metadata. "
            "Open New Topic brief to start a generation, then archive papers."
        )
        st.page_link(
            streamlit_page_for("new_topic_brief"),
            label="Go to New Topic brief",
        )
        st.page_link(
            streamlit_page_for("paper_archiving"),
            label="Go to Paper archiving",
        )
        return

    archiving: PaperArchivingResult = st.session_state[ARCHIVING_RESULT_KEY]
    public_id: UUID = st.session_state[PUBLIC_ID_KEY]
    topic: TopicStatement | None = st.session_state.get(SESSION_KEY)
    paper_ids = _paper_ids(archiving)

    st.caption(f"Reference id: `{public_id}`")
    if topic is not None:
        snippet = topic.text if len(topic.text) <= 200 else f"{topic.text[:197]}..."
        st.write(snippet)

    if not paper_ids:
        st.caption("No archived papers.")
        st.success("Fulfill papers metadata finished for this set.")
        st.caption("Next: Generate paper brief.")
        return

    enqueue_result: FulfillPapersMetadataEnqueueResult | None = st.session_state.get(
        FULFILL_ENQUEUE_RESULT_KEY
    )
    if enqueue_result is None:
        try:
            with session_scope(_session_factory()) as session:
                enqueue_result = enqueue_fulfill_papers_metadata(
                    session,
                    paper_ids,
                    submit_inform=_default_submit_inform,
                )
        except Exception as exc:
            st.error(
                "Could not enqueue fulfill papers metadata. "
                "Check Prefect configuration and try again."
            )
            st.caption(
                prefect_enqueue_error_hint(
                    os.environ.get("PREFECT_API_URL"),
                    INFORM_DEPLOYMENT_REF,
                )
            )
            st.exception(exc)
            return
        st.session_state[FULFILL_ENQUEUE_RESULT_KEY] = enqueue_result

    _render_progress(paper_ids, enqueue_result)
