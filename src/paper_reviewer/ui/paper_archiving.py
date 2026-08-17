"""Paper archiving Streamlit page (create-or-reuse Paper, then ingest progress)."""

from __future__ import annotations

import os
from typing import Any, Mapping
from uuid import UUID

import streamlit as st
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory, session_scope
from paper_reviewer.flows.serve import REGENERATE_PAPER_DEPLOYMENT_REF
from paper_reviewer.models.paper import get_paper_by_id
from paper_reviewer.models.paper_brief import get_paper_brief_by_paper_id
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.paper_archiving import (
    ArchiveSkip,
    ArchiveSkipReason,
    Paper,
    PaperArchivingResult,
    PaperIngestEnqueueResult,
)
from paper_reviewer.schemas.topic_scope.search_external_sources import (
    SearchExternalSourcesResult,
)
from paper_reviewer.schemas.topic_scope.topic_intake import TopicStatement
from paper_reviewer.topic_scope.paper_archiving import (
    archive_papers,
    enqueue_regenerate_papers,
)
from paper_reviewer.ui.external_sources_ingestion import (
    render_external_sources_ingestion_header,
)
from paper_reviewer.ui.search_external_sources import search_cache_matches
from paper_reviewer.ui.topic_scope_url import (
    parse_topic_scope_key,
    workflow_page_link,
)
from paper_reviewer.ui.topic_intake import (
    ARCHIVING_RESULT_KEY,
    PAPER_INGEST_ENQUEUE_RESULT_KEY,
    SEARCH_KEY,
    SESSION_KEY,
)

_SKIP_REASON_LABELS: dict[ArchiveSkipReason, str] = {
    ArchiveSkipReason.missing_doi: "Missing DOI",
    ArchiveSkipReason.invalid_required_field: "Invalid required field",
    ArchiveSkipReason.doi_conflict: "DOI conflict",
}

REGENERATE_BUTTON_LABEL = "Regenerate"
GO_TO_TOPIC_SCOPE_LABEL = "Go to Topic scope"
_ASSISTANT_OUTPUT_HEADING = "Assistant output:"
_TERMINAL_ASPECT_STATUSES = {
    PaperAspectStatus.succeeded,
    PaperAspectStatus.failed,
    PaperAspectStatus.unavailable,
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
    """Return True when search external sources cache matches the URL Topic scope."""
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


def may_submit_regenerate_paper(
    source_record_status: PaperAspectStatus,
    full_text_status: PaperAspectStatus,
) -> bool:
    """Return True when both aspects are terminal so Regenerate is safe to offer."""
    return (
        source_record_status in _TERMINAL_ASPECT_STATUSES
        and full_text_status in _TERMINAL_ASPECT_STATUSES
    )


def split_brief_error_message(error_message: str) -> tuple[str, str | None]:
    """Split a stored brief error into caption text and optional assistant dump."""
    index = error_message.find(_ASSISTANT_OUTPUT_HEADING)
    if index < 0:
        return error_message, None
    caption = error_message[:index].rstrip()
    assistant = error_message[index + len(_ASSISTANT_OUTPUT_HEADING) :].lstrip("\n")
    if not assistant:
        return caption, None
    return caption, assistant


def format_brief_progress_caption(
    *,
    label: str,
    error_message: str | None,
) -> str:
    """Build the brief status fragment; omit any stored assistant dump."""
    if not error_message:
        return f"brief {label}"
    caption_error, _assistant = split_brief_error_message(error_message)
    return f"brief {label} — {caption_error}"


def brief_progress_label(
    *,
    full_text_status: PaperAspectStatus,
    brief_status: PaperAspectStatus | None,
    skipped_already_succeeded: bool,
) -> str:
    """Map full-text gate and brief status to a progress display label."""
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


def paper_ingest_row_is_terminal(
    source_record_status: PaperAspectStatus,
    full_text_status: PaperAspectStatus,
    brief_status: PaperAspectStatus | None,
) -> bool:
    """Return True when this paper needs no more auto-ingest wait."""
    if (
        source_record_status not in _TERMINAL_ASPECT_STATUSES
        or full_text_status not in _TERMINAL_ASPECT_STATUSES
    ):
        return False
    if full_text_status is not PaperAspectStatus.succeeded:
        return True
    return brief_status in _TERMINAL_ASPECT_STATUSES


def render_regenerate_button(
    paper_id: int,
    doi: str,
    *,
    key_prefix: str,
) -> None:
    """Show a secondary Regenerate button that submits regenerate_paper."""
    if st.button(
        REGENERATE_BUTTON_LABEL,
        key=f"{key_prefix}-{paper_id}",
        type="secondary",
    ):
        try:
            from paper_reviewer.flows.submit import submit_regenerate_paper

            submit_regenerate_paper(paper_id, doi)
        except Exception as exc:
            st.error(
                "Could not enqueue regenerate paper. "
                "Check Prefect configuration and try again."
            )
            st.caption(
                prefect_enqueue_error_hint(
                    os.environ.get("PREFECT_API_URL"),
                    REGENERATE_PAPER_DEPLOYMENT_REF,
                )
            )
            st.exception(exc)


def _default_submit_regenerate(paper_id: int, doi: str) -> None:
    """Submit one regenerate_paper job (Prefect wiring in Compose)."""
    from paper_reviewer.flows.submit import submit_regenerate_paper

    submit_regenerate_paper(paper_id, doi)


def _paper_ids(archiving: PaperArchivingResult) -> list[int]:
    return [paper.id for paper in archiving.papers]


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


def _render_archive_sections(
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


@st.fragment(run_every=2)
def _render_progress(
    paper_ids: list[int],
    enqueue_result: PaperIngestEnqueueResult,
    *,
    topic_scope_key: UUID,
) -> None:
    skipped_existed = set(enqueue_result.skipped_already_existed)
    all_terminal = True

    with session_scope(_session_factory()) as session:
        rows: list[dict[str, Any]] = []
        for paper_id in paper_ids:
            paper = get_paper_by_id(session, paper_id)
            if paper is None:
                continue
            brief = get_paper_brief_by_paper_id(session, paper_id)
            brief_status = brief.status if brief is not None else None
            source_status = paper.source_record_status
            full_text_status = paper.full_text_status
            skipped = paper_id in skipped_existed
            source_label = aspect_status_label(
                status=source_status,
                skipped_already_succeeded=(
                    skipped and source_status is PaperAspectStatus.succeeded
                ),
            )
            full_text_label = aspect_status_label(
                status=full_text_status,
                skipped_already_succeeded=(
                    skipped and full_text_status is PaperAspectStatus.succeeded
                ),
            )
            brief_label = brief_progress_label(
                full_text_status=full_text_status,
                brief_status=brief_status,
                skipped_already_succeeded=(
                    skipped and brief_status is PaperAspectStatus.succeeded
                ),
            )
            if not paper_ingest_row_is_terminal(
                source_status,
                full_text_status,
                brief_status,
            ):
                all_terminal = False
            brief_error = None
            if (
                brief is not None
                and brief.status is PaperAspectStatus.failed
                and brief.error_message
            ):
                brief_error = brief.error_message
            aspect_error = _aspect_error_text(
                source_record_status=source_status,
                source_record_error_message=paper.source_record_error_message,
                full_text_status=full_text_status,
                full_text_error_message=paper.full_text_error_message,
            )
            rows.append(
                {
                    "paper_id": paper_id,
                    "title": paper.title,
                    "url": paper.url,
                    "doi": paper.doi,
                    "source_status": source_status,
                    "full_text_status": full_text_status,
                    "source_label": source_label,
                    "full_text_label": full_text_label,
                    "brief_label": brief_label,
                    "brief_error": brief_error,
                    "aspect_error": aspect_error,
                    "pmc_article_url": paper.pmc_article_url,
                    "open_access_pdf_url": paper.open_access_pdf_url,
                }
            )

    st.subheader("Progress")
    if not rows:
        st.caption("No archived papers.")
        workflow_page_link(
            "topic_scope",
            label=GO_TO_TOPIC_SCOPE_LABEL,
            topic_scope_key=topic_scope_key,
        )
        return

    for row in rows:
        st.markdown(f"**[{row['title']}]({row['url']})**")
        aspect_part = f" — {row['aspect_error']}" if row["aspect_error"] else ""
        brief_part = format_brief_progress_caption(
            label=row["brief_label"],
            error_message=row["brief_error"],
        )
        st.caption(
            f"DOI `{row['doi']}` · source record {row['source_label']} · "
            f"full text {row['full_text_label']} · {brief_part}{aspect_part}"
        )
        links = enrichment_links_caption(
            row["pmc_article_url"],
            row["open_access_pdf_url"],
        )
        if links:
            st.caption(links)
        if row["brief_error"]:
            _, assistant = split_brief_error_message(row["brief_error"])
            if assistant:
                with st.expander("Assistant output"):
                    st.text(assistant)
        if may_submit_regenerate_paper(
            row["source_status"],
            row["full_text_status"],
        ):
            render_regenerate_button(
                row["paper_id"],
                row["doi"],
                key_prefix="regenerate-archiving",
            )

    if all_terminal:
        st.success("Paper ingest finished for this set.")
        workflow_page_link(
            "topic_scope",
            label=GO_TO_TOPIC_SCOPE_LABEL,
            topic_scope_key=topic_scope_key,
        )


def _enqueue_ingest(archiving: PaperArchivingResult) -> PaperIngestEnqueueResult:
    with session_scope(_session_factory()) as session:
        return enqueue_regenerate_papers(
            session,
            archiving,
            submit_regenerate=_default_submit_regenerate,
        )


def render_paper_archiving() -> None:
    """Render the Paper archiving page."""
    topic_scope_key = parse_topic_scope_key(st.query_params)
    render_external_sources_ingestion_header(
        current_page_key="paper_archiving",
        topic_scope_key=topic_scope_key,
    )
    st.header("Paper archiving")

    if not archiving_prerequisites_met(
        st.session_state,
        topic_scope_key=topic_scope_key,
    ):
        st.info(
            "Run search external sources before paper archiving. "
            "Open Topic intake to start a Topic scope, then search external sources."
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
            "search_external_sources",
            label="Go to Search external sources",
            topic_scope_key=topic_scope_key,
        )
        return

    search_result: SearchExternalSourcesResult = st.session_state[SEARCH_KEY]
    candidates = search_result.candidates
    topic: TopicStatement | None = st.session_state.get(SESSION_KEY)

    if topic_scope_key is not None:
        st.caption(f"Reference id: `{topic_scope_key}`")
    if topic is not None:
        snippet = topic.text if len(topic.text) <= 200 else f"{topic.text[:197]}..."
        st.write(snippet)

    cached: PaperArchivingResult | None = st.session_state.get(ARCHIVING_RESULT_KEY)
    if cached is None:
        try:
            with st.spinner("Archiving papers…"):
                with session_scope(_session_factory()) as session:
                    archiving_result = archive_papers(session, candidates)
        except Exception:
            st.error("Paper archiving failed. Try again from Search external sources.")
            return
        st.session_state[ARCHIVING_RESULT_KEY] = archiving_result
        st.session_state.pop(PAPER_INGEST_ENQUEUE_RESULT_KEY, None)
        cached = archiving_result

    _render_archive_sections(
        cached,
        input_count=len(candidates),
        topic_scope_key=topic_scope_key,
    )

    if topic_scope_key is None:
        return

    enqueue_result: PaperIngestEnqueueResult | None = st.session_state.get(
        PAPER_INGEST_ENQUEUE_RESULT_KEY
    )
    if enqueue_result is None:
        try:
            enqueue_result = _enqueue_ingest(cached)
        except Exception as exc:
            st.error(
                "Could not enqueue paper ingest. "
                "Check Prefect configuration and try again."
            )
            st.caption(
                prefect_enqueue_error_hint(
                    os.environ.get("PREFECT_API_URL"),
                    REGENERATE_PAPER_DEPLOYMENT_REF,
                )
            )
            st.exception(exc)
            return
        st.session_state[PAPER_INGEST_ENQUEUE_RESULT_KEY] = enqueue_result

    _render_progress(
        _paper_ids(cached),
        enqueue_result,
        topic_scope_key=topic_scope_key,
    )
