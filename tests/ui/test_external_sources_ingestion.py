"""External sources ingestion landing: registration, phase header, and stepper."""

from __future__ import annotations

import inspect

from paper_reviewer.ui.external_sources_ingestion import (
    CONTINUE_TO_SEARCH_EXTERNAL_SOURCES_LABEL,
    CURRENT_STEP_BADGE,
    EXTERNAL_SOURCES_INGESTION_STEPS,
    GO_TO_TOPIC_INTAKE_LABEL,
    GO_TO_TOPIC_SCOPE_LABEL,
    INTRO_TEXT,
    MISSING_SCOPE_MESSAGE,
    PHASE_TITLE,
    SEARCH_EXTERNAL_SOURCES_PAGE_KEY,
    external_sources_ingestion_stepper_items,
    render_external_sources_ingestion,
    render_external_sources_ingestion_header,
)
from paper_reviewer.ui.fulfill_papers_metadata import render_fulfill_papers_metadata
from paper_reviewer.ui.generate_paper_brief import render_generate_paper_brief
from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.paper_archiving import render_paper_archiving
from paper_reviewer.ui.search_external_sources import render_search_external_sources


def test_render_external_sources_ingestion_is_public() -> None:
    assert callable(render_external_sources_ingestion)


def test_render_external_sources_ingestion_header_is_public() -> None:
    assert callable(render_external_sources_ingestion_header)


def test_external_sources_ingestion_render_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert pages["external_sources_ingestion"].render is (
        render_external_sources_ingestion
    )
    assert pages["external_sources_ingestion"].title == (
        "External sources ingestion"
    )
    assert pages["external_sources_ingestion"].url_path == (
        "external-sources-ingestion"
    )
    assert pages["external_sources_ingestion"].in_sidebar is False


def test_phase_title_copy() -> None:
    assert PHASE_TITLE == "External sources ingestion"


def test_missing_key_copy_links_to_intake_and_hub() -> None:
    assert MISSING_SCOPE_MESSAGE == (
        "Open Topic intake to create a Topic scope, then open External sources "
        "ingestion from the Topic scope hub."
    )
    assert GO_TO_TOPIC_INTAKE_LABEL == "Go to Topic intake"
    assert GO_TO_TOPIC_SCOPE_LABEL == "Go to Topic scope"


def test_intro_and_primary_link_target_search_external_sources() -> None:
    assert INTRO_TEXT == (
        "This phase searches external sources and ingests papers for this Topic scope."
    )
    assert SEARCH_EXTERNAL_SOURCES_PAGE_KEY == "search_external_sources"
    assert CONTINUE_TO_SEARCH_EXTERNAL_SOURCES_LABEL == (
        "Continue to Search external sources"
    )


def test_external_sources_ingestion_steps_are_the_ingest_chain() -> None:
    assert EXTERNAL_SOURCES_INGESTION_STEPS == (
        ("search_external_sources", "Search external sources"),
        ("paper_archiving", "Paper archiving"),
        ("fulfill_papers_metadata", "Fulfill papers metadata"),
        ("generate_paper_brief", "Generate paper brief"),
    )


def test_landing_marks_no_step_current() -> None:
    items = external_sources_ingestion_stepper_items("external_sources_ingestion")

    assert [item.page_key for item in items] == [
        key for key, _label in EXTERNAL_SOURCES_INGESTION_STEPS
    ]
    assert [item.step_number for item in items] == [1, 2, 3, 4]
    assert all(item.is_current is False for item in items)


def test_stepper_marks_only_the_current_step() -> None:
    items = external_sources_ingestion_stepper_items("paper_archiving")
    current = [item for item in items if item.is_current]

    assert len(current) == 1
    assert current[0].page_key == "paper_archiving"
    assert current[0].label == "Paper archiving"
    assert current[0].step_number == 2


def test_unknown_page_marks_no_step_current() -> None:
    items = external_sources_ingestion_stepper_items("topic_scope")

    assert all(item.is_current is False for item in items)


def test_current_step_badge_copy() -> None:
    assert CURRENT_STEP_BADGE == "Current"


def test_phase_header_owns_the_phase_title() -> None:
    source = inspect.getsource(render_external_sources_ingestion_header)
    assert "st.title" in source
    assert "PHASE_TITLE" in source


def test_landing_empty_state_shows_phase_title_without_header() -> None:
    source = inspect.getsource(render_external_sources_ingestion)
    assert "st.title" in source
    assert "PHASE_TITLE" in source
    assert "render_external_sources_ingestion_header" in source


def test_ingest_pages_render_the_phase_header() -> None:
    renders = (
        render_external_sources_ingestion,
        render_search_external_sources,
        render_paper_archiving,
        render_fulfill_papers_metadata,
        render_generate_paper_brief,
    )
    for render in renders:
        source = inspect.getsource(render)
        assert "render_external_sources_ingestion_header" in source, render.__name__


def test_ingest_step_pages_use_header_not_title_for_step_name() -> None:
    renders = (
        render_search_external_sources,
        render_paper_archiving,
        render_fulfill_papers_metadata,
        render_generate_paper_brief,
    )
    for render in renders:
        source = inspect.getsource(render)
        assert "st.header" in source, render.__name__
        assert "st.title" not in source, render.__name__
