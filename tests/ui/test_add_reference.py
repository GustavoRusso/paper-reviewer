"""Add reference page: registration, Papers search results, per-paper Add."""

from __future__ import annotations

import inspect

from paper_reviewer.schemas.topic_brief_generation.papers_search import (
    PaperSearchHit,
)
from paper_reviewer.ui import add_reference as add_reference_module
from paper_reviewer.ui.add_reference import (
    ADD_ALL_BUTTON_LABEL,
    ADD_BUTTON_LABEL,
    ALREADY_REFERENCED_BADGE,
    ATTACH_ERROR_MESSAGE,
    EMPTY_NO_CONCEPTS_CAPTION,
    EMPTY_NO_HITS_CAPTION,
    GO_TO_SHOW_REFERENCES_LABEL,
    GO_TO_TOPIC_INTAKE_LABEL,
    GO_TO_TOPIC_SCOPE_LABEL,
    LOAD_ERROR_MESSAGE,
    MISSING_SCOPE_MESSAGE,
    NOT_YET_REFERENCED_BADGE,
    PAPER_BRIEF_AVAILABLE_BADGE,
    PAPER_BRIEF_NOT_AVAILABLE_BADGE,
    TRUNCATED_CAPTION,
    format_paper_search_hit_caption,
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


def test_page_uses_phase_header_then_step_header() -> None:
    source = inspect.getsource(render_add_reference)
    assert "render_references_selection_header" in source
    assert 'current_page_key="add_reference"' in source
    assert "st.header" in source
    assert "st.title" not in source


def test_page_does_not_repeat_reference_id_caption() -> None:
    source = inspect.getsource(render_add_reference)
    assert "Reference id:" not in source


def test_page_loads_scope_and_runs_papers_search() -> None:
    source = inspect.getsource(render_add_reference)
    assert "get_topic_scope_by_key" in source
    assert "search_papers" in source
    assert "session_scope" in source


def test_missing_topic_scope_row_uses_the_same_empty_state() -> None:
    source = inspect.getsource(render_add_reference)
    assert "_render_missing_scope" in source
    assert "topic_scope is None" in source


def test_empty_and_load_error_copy() -> None:
    assert EMPTY_NO_CONCEPTS_CAPTION == (
        "No topic facet concepts to search. Run Topic analysis first."
    )
    assert EMPTY_NO_HITS_CAPTION == (
        "No ingested papers match this Topic scope's concepts."
    )
    assert TRUNCATED_CAPTION == "Showing the first 20 matching papers."
    assert LOAD_ERROR_MESSAGE == (
        "Could not load Papers search for this Topic scope. Try again."
    )


def test_badge_labels() -> None:
    assert ALREADY_REFERENCED_BADGE == "Already a Reference"
    assert NOT_YET_REFERENCED_BADGE == "Not yet a Reference"
    assert PAPER_BRIEF_AVAILABLE_BADGE == "Paper brief available"
    assert PAPER_BRIEF_NOT_AVAILABLE_BADGE == "Paper brief not available"


def test_add_button_copy_and_attach_error() -> None:
    assert ADD_BUTTON_LABEL == "Add"
    assert ADD_ALL_BUTTON_LABEL == "Add all results"
    assert ATTACH_ERROR_MESSAGE == (
        "Could not add References for this Topic scope. Try again."
    )
    assert GO_TO_SHOW_REFERENCES_LABEL == "Go to Show references"


def test_page_links_back_to_show_references() -> None:
    source = inspect.getsource(add_reference_module)
    assert '"show_references"' in source
    assert "GO_TO_SHOW_REFERENCES_LABEL" in source


def test_page_offers_add_on_not_yet_hits_only() -> None:
    source = inspect.getsource(add_reference_module)
    assert "ADD_BUTTON_LABEL" in source
    assert 'type="secondary"' in source
    assert "add_references" in source
    assert "st.rerun" in source
    assert "already_referenced" in source


def test_page_offers_add_all_for_not_yet_hits() -> None:
    source = inspect.getsource(add_reference_module)
    assert "ADD_ALL_BUTTON_LABEL" in source
    render_source = inspect.getsource(render_add_reference)
    assert "_render_add_all" in render_source
    add_all_source = inspect.getsource(add_reference_module._render_add_all)
    assert "already_referenced" in add_all_source
    assert 'key="add-all-references"' in add_all_source
    assert 'type="secondary"' in add_all_source


def test_page_does_not_show_attach_not_built_caption() -> None:
    source = inspect.getsource(add_reference_module)
    assert "ATTACH_NOT_BUILT_CAPTION" not in source
    assert "not built yet" not in source


def test_page_renders_hit_card_with_badge() -> None:
    source = inspect.getsource(add_reference_module)
    assert "format_paper_search_hit_caption" in source
    assert "st.markdown" in source
    assert "st.badge" in source
    assert "ALREADY_REFERENCED_BADGE" in source
    assert "NOT_YET_REFERENCED_BADGE" in source
    assert "PAPER_BRIEF_AVAILABLE_BADGE" in source
    assert "PAPER_BRIEF_NOT_AVAILABLE_BADGE" in source
    assert "paper_brief_available" in source


def test_format_paper_search_hit_caption() -> None:
    hit = PaperSearchHit(
        title="Example",
        url="https://example.com/1",
        doi="10.1000/A",
        authors=["Ada Lovelace", "Alan Turing"],
        journal="Nature",
        published_year=2024,
        already_referenced=False,
        paper_brief_available=True,
    )

    assert format_paper_search_hit_caption(hit) == (
        "Ada Lovelace, Alan Turing · Nature · 2024 · DOI `10.1000/A`"
    )


def test_format_paper_search_hit_caption_missing_optional_fields() -> None:
    hit = PaperSearchHit(
        title="Untitled",
        url="https://example.com/2",
        doi="10.1000/B",
        authors=[],
        journal=None,
        published_year=None,
        already_referenced=True,
        paper_brief_available=False,
    )

    assert format_paper_search_hit_caption(hit) == (
        "— · — · — · DOI `10.1000/B`"
    )
