"""Paper ingestion phase landing Streamlit page."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import streamlit as st

from paper_reviewer.ui.topic_scope_url import (
    parse_topic_scope_key,
    workflow_page_link,
)

INTRO_TEXT = (
    "This phase searches paper sources and ingests papers for this Topic scope."
)
MISSING_SCOPE_MESSAGE = (
    "Open Topic intake to create a Topic scope, then open Paper ingestion from "
    "the Topic scope hub."
)
GO_TO_TOPIC_INTAKE_LABEL = "Go to Topic intake"
GO_TO_TOPIC_SCOPE_LABEL = "Go to Topic scope"
RELATED_PAPER_SEARCH_PAGE_KEY = "related_paper_search"
CONTINUE_TO_RELATED_PAPER_SEARCH_LABEL = "Continue to Related-paper search"
CURRENT_STEP_BADGE = "Current"
PAPER_INGESTION_STEPS: tuple[tuple[str, str], ...] = (
    ("related_paper_search", "Related-paper search"),
    ("paper_archiving", "Paper archiving"),
    ("fulfill_papers_metadata", "Fulfill papers metadata"),
    ("generate_paper_brief", "Generate paper brief"),
)


@dataclass(frozen=True)
class PhaseStepperItem:
    """One step in a phase progress stepper."""

    page_key: str
    label: str
    step_number: int
    is_current: bool


def paper_ingestion_stepper_items(
    current_page_key: str,
) -> tuple[PhaseStepperItem, ...]:
    """Return stepper items for Paper ingestion, marking the current step."""
    return tuple(
        PhaseStepperItem(
            page_key=page_key,
            label=label,
            step_number=index,
            is_current=page_key == current_page_key,
        )
        for index, (page_key, label) in enumerate(PAPER_INGESTION_STEPS, start=1)
    )


def render_paper_ingestion_header(
    *,
    current_page_key: str,
    topic_scope_key: UUID | None,
) -> None:
    """Show the phase description and a stepper of ingest steps."""
    st.write(INTRO_TEXT)
    items = paper_ingestion_stepper_items(current_page_key)
    columns = st.columns(len(items))
    for column, item in zip(columns, items, strict=True):
        with column:
            caption = f"{item.step_number}. {item.label}"
            if item.is_current:
                st.markdown(f"**{caption}**")
                st.badge(CURRENT_STEP_BADGE)
            else:
                workflow_page_link(
                    item.page_key,
                    label=caption,
                    topic_scope_key=topic_scope_key,
                )
    st.divider()


def _render_missing_scope() -> None:
    st.info(MISSING_SCOPE_MESSAGE)
    workflow_page_link(
        "topic_intake",
        label=GO_TO_TOPIC_INTAKE_LABEL,
        topic_scope_key=None,
    )
    workflow_page_link(
        "topic_scope",
        label=GO_TO_TOPIC_SCOPE_LABEL,
        topic_scope_key=None,
    )


def render_paper_ingestion() -> None:
    """Render the Paper ingestion landing for the Topic scope in the URL."""
    st.title("Paper ingestion")
    topic_scope_key = parse_topic_scope_key(st.query_params)
    if topic_scope_key is None:
        _render_missing_scope()
        return

    st.caption(f"Reference id: `{topic_scope_key}`")
    render_paper_ingestion_header(
        current_page_key="paper_ingestion",
        topic_scope_key=topic_scope_key,
    )
    workflow_page_link(
        RELATED_PAPER_SEARCH_PAGE_KEY,
        label=CONTINUE_TO_RELATED_PAPER_SEARCH_LABEL,
        topic_scope_key=topic_scope_key,
    )
