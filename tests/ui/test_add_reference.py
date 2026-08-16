"""Add reference stub page: registration, missing key, and not-built copy."""

from __future__ import annotations

import inspect

from paper_reviewer.ui.add_reference import (
    GO_TO_SHOW_REFERENCES_LABEL,
    GO_TO_TOPIC_INTAKE_LABEL,
    GO_TO_TOPIC_SCOPE_LABEL,
    MISSING_SCOPE_MESSAGE,
    NOT_BUILT_CAPTION,
    render_add_reference,
)
from paper_reviewer.ui.navigation import build_app_pages


def test_render_add_reference_is_public() -> None:
    assert callable(render_add_reference)


def test_add_reference_render_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert pages["add_reference"].render is render_add_reference
    assert pages["add_reference"].title == "Add reference"
    assert pages["add_reference"].url_path == "add-reference"
    assert pages["add_reference"].in_sidebar is False


def test_missing_key_copy_links_to_intake_and_hub() -> None:
    assert MISSING_SCOPE_MESSAGE == (
        "Open Topic intake to create a Topic scope, then open Add reference "
        "from References selection."
    )
    assert GO_TO_TOPIC_INTAKE_LABEL == "Go to Topic intake"
    assert GO_TO_TOPIC_SCOPE_LABEL == "Go to Topic scope"


def test_not_built_caption_and_back_link() -> None:
    assert NOT_BUILT_CAPTION == (
        "Attaching References from local search results is not built yet."
    )
    assert GO_TO_SHOW_REFERENCES_LABEL == "Go to Show references"


def test_page_uses_phase_header_then_step_header() -> None:
    source = inspect.getsource(render_add_reference)
    assert "render_references_selection_header" in source
    assert 'current_page_key="add_reference"' in source
    assert "st.header" in source
    assert "st.title" not in source


def test_page_links_back_to_show_references() -> None:
    source = inspect.getsource(render_add_reference)
    assert '"show_references"' in source
    assert "GO_TO_SHOW_REFERENCES_LABEL" in source
