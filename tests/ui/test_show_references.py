"""Show references page: registration, missing key, empty list, and chrome."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime

from paper_reviewer.schemas.topic_brief_generation.show_references import (
    ReferencedPaper,
)
from paper_reviewer.ui import show_references as show_references_module
from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.show_references import (
    CONTINUE_TO_ADD_REFERENCE_LABEL,
    EMPTY_REFERENCES_CAPTION,
    GO_TO_REFERENCES_SELECTION_LABEL,
    GO_TO_TOPIC_INTAKE_LABEL,
    GO_TO_TOPIC_SCOPE_LABEL,
    MISSING_SCOPE_MESSAGE,
    PAPER_BRIEF_AVAILABLE_BADGE,
    PAPER_BRIEF_NOT_AVAILABLE_BADGE,
    format_referenced_paper_caption,
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


def test_page_loads_scope_and_references_from_the_database() -> None:
    source = inspect.getsource(render_show_references)
    assert "get_topic_scope_by_key" in source
    assert "list_show_references" in source
    assert "session_scope" in source


def test_missing_topic_scope_row_uses_the_same_empty_state() -> None:
    source = inspect.getsource(render_show_references)
    assert "_render_missing_scope" in source
    assert "topic_scope is None" in source


def test_page_links_to_add_reference_hub_and_landing() -> None:
    source = inspect.getsource(show_references_module)
    assert '"add_reference"' in source
    assert "CONTINUE_TO_ADD_REFERENCE_LABEL" in source
    assert '"topic_scope"' in source
    assert '"references_selection"' in source


def test_paper_brief_badge_labels() -> None:
    assert PAPER_BRIEF_AVAILABLE_BADGE == "Paper brief available"
    assert PAPER_BRIEF_NOT_AVAILABLE_BADGE == "Paper brief not available"


def test_format_referenced_paper_caption() -> None:
    paper = ReferencedPaper(
        title="Example",
        url="https://example.com/1",
        doi="10.1000/A",
        authors=["Ada Lovelace", "Alan Turing"],
        journal="Nature",
        published_year=2024,
        referenced_at=datetime(2026, 1, 2, tzinfo=UTC),
        paper_brief_available=True,
    )

    assert format_referenced_paper_caption(paper) == (
        "Ada Lovelace, Alan Turing · Nature · 2024 · DOI `10.1000/A`"
    )


def test_format_referenced_paper_caption_missing_optional_fields() -> None:
    paper = ReferencedPaper(
        title="Untitled",
        url="https://example.com/2",
        doi="10.1000/B",
        authors=[],
        journal=None,
        published_year=None,
        referenced_at=datetime(2026, 1, 2, tzinfo=UTC),
        paper_brief_available=False,
    )

    assert format_referenced_paper_caption(paper) == (
        "— · — · — · DOI `10.1000/B`"
    )


def test_page_renders_title_as_content_link() -> None:
    source = inspect.getsource(show_references_module)
    assert "format_referenced_paper_caption" in source
    assert "st.markdown" in source
    assert "paper.title" in source
    assert "paper.url" in source


def test_page_renders_paper_brief_badge() -> None:
    source = inspect.getsource(show_references_module)
    assert "st.badge" in source
    assert "PAPER_BRIEF_AVAILABLE_BADGE" in source
    assert "PAPER_BRIEF_NOT_AVAILABLE_BADGE" in source
    assert "paper_brief_available" in source
