"""References selection phase chrome: header and stepper."""

from __future__ import annotations

import inspect

from paper_reviewer.ui.add_reference import render_add_reference
from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.references_selection import (
    CURRENT_STEP_BADGE,
    INTRO_TEXT,
    PHASE_TITLE,
    REFERENCES_SELECTION_STEPS,
    references_selection_stepper_items,
    render_references_selection_header,
)
from paper_reviewer.ui.show_references import render_show_references


def test_render_references_selection_header_is_public() -> None:
    assert callable(render_references_selection_header)


def test_references_selection_landing_is_not_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "references_selection" not in pages


def test_phase_title_copy() -> None:
    assert PHASE_TITLE == "References selection"


def test_intro_copy() -> None:
    assert INTRO_TEXT == (
        "This phase selects ingested papers as References for this Topic scope."
    )


def test_references_selection_steps_are_the_leaf_steps() -> None:
    assert REFERENCES_SELECTION_STEPS == (
        ("show_references", "Show references"),
        ("add_reference", "Add reference"),
    )


def test_stepper_marks_only_the_current_step() -> None:
    items = references_selection_stepper_items("add_reference")
    current = [item for item in items if item.is_current]

    assert len(current) == 1
    assert current[0].page_key == "add_reference"
    assert current[0].label == "Add reference"
    assert current[0].step_number == 2


def test_show_references_marks_step_current() -> None:
    items = references_selection_stepper_items("show_references")
    current = [item for item in items if item.is_current]

    assert len(current) == 1
    assert current[0].page_key == "show_references"
    assert current[0].step_number == 1


def test_unknown_page_marks_no_step_current() -> None:
    items = references_selection_stepper_items("topic_scope")

    assert all(item.is_current is False for item in items)


def test_current_step_badge_copy() -> None:
    assert CURRENT_STEP_BADGE == "Current"


def test_phase_header_owns_the_phase_title() -> None:
    source = inspect.getsource(render_references_selection_header)
    assert "st.title" in source
    assert "PHASE_TITLE" in source


def test_phase_pages_render_the_phase_header() -> None:
    renders = (
        render_show_references,
        render_add_reference,
    )
    for render in renders:
        source = inspect.getsource(render)
        assert "render_references_selection_header" in source, render.__name__


def test_step_pages_use_header_not_title_for_step_name() -> None:
    renders = (
        render_show_references,
        render_add_reference,
    )
    for render in renders:
        source = inspect.getsource(render)
        assert "st.header" in source, render.__name__
        assert "st.title" not in source, render.__name__
