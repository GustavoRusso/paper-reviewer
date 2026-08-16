"""Show references page: registration, missing key, empty list, and chrome."""

from __future__ import annotations

import inspect

from paper_reviewer.ui import show_references as show_references_module
from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.show_references import (
    CONTINUE_TO_ADD_REFERENCE_LABEL,
    EMPTY_REFERENCES_CAPTION,
    GO_TO_REFERENCES_SELECTION_LABEL,
    GO_TO_TOPIC_INTAKE_LABEL,
    GO_TO_TOPIC_SCOPE_LABEL,
    MISSING_SCOPE_MESSAGE,
    render_show_references,
)


def test_render_show_references_is_public() -> None:
    assert callable(render_show_references)


def test_show_references_render_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert pages["show_references"].render is render_show_references
    assert pages["show_references"].title == "Show references"
    assert pages["show_references"].url_path == "show-references"
    assert pages["show_references"].in_sidebar is False


def test_missing_key_copy_links_to_intake_and_hub() -> None:
    assert MISSING_SCOPE_MESSAGE == (
        "Open Topic intake to create a Topic scope, then open Show references "
        "from References selection."
    )
    assert GO_TO_TOPIC_INTAKE_LABEL == "Go to Topic intake"
    assert GO_TO_TOPIC_SCOPE_LABEL == "Go to Topic scope"


def test_empty_list_copy_and_navigation_labels() -> None:
    assert EMPTY_REFERENCES_CAPTION == (
        "This Topic scope has no References yet."
    )
    assert CONTINUE_TO_ADD_REFERENCE_LABEL == "Continue to Add reference"
    assert GO_TO_REFERENCES_SELECTION_LABEL == "Go to References selection"


def test_page_uses_phase_header_then_step_header() -> None:
    source = inspect.getsource(render_show_references)
    assert "render_references_selection_header" in source
    assert 'current_page_key="show_references"' in source
    assert "st.header" in source
    assert "st.title" not in source


def test_page_does_not_repeat_reference_id_caption() -> None:
    source = inspect.getsource(render_show_references)
    assert "Reference id:" not in source


def test_page_links_to_add_reference_hub_and_landing() -> None:
    source = inspect.getsource(show_references_module)
    assert '"add_reference"' in source
    assert "CONTINUE_TO_ADD_REFERENCE_LABEL" in source
    assert '"topic_scope"' in source
    assert '"references_selection"' in source
