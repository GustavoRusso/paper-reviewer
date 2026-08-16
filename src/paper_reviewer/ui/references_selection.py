"""References selection phase landing Streamlit page."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import streamlit as st

from paper_reviewer.ui.topic_scope_url import (
    parse_topic_scope_key,
    workflow_page_link,
)

PHASE_TITLE = "References selection"
INTRO_TEXT = (
    "This phase selects ingested papers as References for this Topic scope."
)
MISSING_SCOPE_MESSAGE = (
    "Open Topic intake to create a Topic scope, then open References "
    "selection from the Topic scope hub."
)
GO_TO_TOPIC_INTAKE_LABEL = "Go to Topic intake"
GO_TO_TOPIC_SCOPE_LABEL = "Go to Topic scope"
SHOW_REFERENCES_PAGE_KEY = "show_references"
CONTINUE_TO_SHOW_REFERENCES_LABEL = "Continue to Show references"
CURRENT_STEP_BADGE = "Current"
REFERENCES_SELECTION_STEPS: tuple[tuple[str, str], ...] = (
    ("show_references", "Show references"),
    ("add_reference", "Add reference"),
)


@dataclass(frozen=True)
class PhaseStepperItem:
    """One step in a phase progress stepper."""

    page_key: str
    label: str
    step_number: int
    is_current: bool


def references_selection_stepper_items(
    current_page_key: str,
) -> tuple[PhaseStepperItem, ...]:
    """Return stepper items for References selection, marking the current step."""
    return tuple(
        PhaseStepperItem(
            page_key=page_key,
            label=label,
            step_number=index,
            is_current=page_key == current_page_key,
        )
        for index, (page_key, label) in enumerate(
            REFERENCES_SELECTION_STEPS, start=1
        )
    )


def render_references_selection_header(
    *,
    current_page_key: str,
    topic_scope_key: UUID | None,
) -> None:
    """Show the phase title, Reference id, intro, and a stepper of leaf steps."""
    st.title(PHASE_TITLE)
    if topic_scope_key is not None:
        st.caption(f"Reference id: `{topic_scope_key}`")
    st.write(INTRO_TEXT)
    items = references_selection_stepper_items(current_page_key)
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


def render_references_selection() -> None:
    """Render the References selection landing for the Topic scope in the URL."""
    topic_scope_key = parse_topic_scope_key(st.query_params)
    if topic_scope_key is None:
        st.title(PHASE_TITLE)
        _render_missing_scope()
        return

    render_references_selection_header(
        current_page_key="references_selection",
        topic_scope_key=topic_scope_key,
    )
    workflow_page_link(
        SHOW_REFERENCES_PAGE_KEY,
        label=CONTINUE_TO_SHOW_REFERENCES_LABEL,
        topic_scope_key=topic_scope_key,
    )
