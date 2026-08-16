"""References selection landing: registration, phase header, and stepper."""

from __future__ import annotations

import inspect

from paper_reviewer.ui.add_reference import render_add_reference
from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.references_selection import (
    CONTINUE_TO_SHOW_REFERENCES_LABEL,
    CURRENT_STEP_BADGE,
    GO_TO_TOPIC_INTAKE_LABEL,
    GO_TO_TOPIC_SCOPE_LABEL,
    INTRO_TEXT,
    MISSING_SCOPE_MESSAGE,
    PHASE_TITLE,
    REFERENCES_SELECTION_STEPS,
    SHOW_REFERENCES_PAGE_KEY,
    references_selection_stepper_items,
    render_references_selection,
    render_references_selection_header,
)
from paper_reviewer.ui.show_references import render_show_references


def test_render_references_selection_is_public() -> None:
    assert callable(render_references_selection)


def test_render_references_selection_header_is_public() -> None:
    assert callable(render_references_selection_header)


def test_references_selection_render_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert pages["references_selection"].render is render_references_selection
    assert pages["references_selection"].title == "References selection"
    assert pages["references_selection"].url_path == "references-selection"
    assert pages["references_selection"].in_sidebar is False


def test_phase_title_copy() -> None:
    assert PHASE_TITLE == "References selection"


def test_missing_key_copy_links_to_intake_and_hub() -> None:
    assert MISSING_SCOPE_MESSAGE == (
        "Open Topic intake to create a Topic scope, then open References "
        "selection from the Topic scope hub."
    )
    assert GO_TO_TOPIC_INTAKE_LABEL == "Go to Topic intake"
    assert GO_TO_TOPIC_SCOPE_LABEL == "Go to Topic scope"


def test_intro_and_primary_link_target_show_references() -> None:
    assert INTRO_TEXT == (
        "This phase selects ingested papers as References for this Topic scope."
    )
    assert SHOW_REFERENCES_PAGE_KEY == "show_references"
    assert CONTINUE_TO_SHOW_REFERENCES_LABEL == "Continue to Show references"


def test_references_selection_steps_are_the_leaf_steps() -> None:
    assert REFERENCES_SELECTION_STEPS == (
        ("show_references", "Show references"),
        ("add_reference", "Add reference"),
    )


def test_landing_marks_no_step_current() -> None:
    items = references_selection_stepper_items("references_selection")

    assert [item.page_key for item in items] == [
        key for key, _label in REFERENCES_SELECTION_STEPS
    ]
    assert [item.step_number for item in items] == [1, 2]
    assert all(item.is_current is False for item in items)


def test_stepper_marks_only_the_current_step() -> None:
    items = references_selection_stepper_items("add_reference")
    current = [item for item in items if item.is_current]

    assert len(current) == 1
    assert current[0].page_key == "add_reference"
    assert current[0].label == "Add reference"
    assert current[0].step_number == 2


def test_unknown_page_marks_no_step_current() -> None:
    items = references_selection_stepper_items("topic_scope")

    assert all(item.is_current is False for item in items)


def test_current_step_badge_copy() -> None:
    assert CURRENT_STEP_BADGE == "Current"


def test_phase_header_owns_the_phase_title() -> None:
    source = inspect.getsource(render_references_selection_header)
    assert "st.title" in source
    assert "PHASE_TITLE" in source


def test_landing_empty_state_shows_phase_title_without_header() -> None:
    source = inspect.getsource(render_references_selection)
    assert "st.title" in source
    assert "PHASE_TITLE" in source
    assert "render_references_selection_header" in source


def test_phase_pages_render_the_phase_header() -> None:
    renders = (
        render_references_selection,
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
