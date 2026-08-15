"""Paper ingestion landing: registration, phase header, and stepper."""

from __future__ import annotations

import inspect

from paper_reviewer.ui.fulfill_papers_metadata import render_fulfill_papers_metadata
from paper_reviewer.ui.generate_paper_brief import render_generate_paper_brief
from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.paper_archiving import render_paper_archiving
from paper_reviewer.ui.paper_ingestion import (
    CONTINUE_TO_RELATED_PAPER_SEARCH_LABEL,
    CURRENT_STEP_BADGE,
    GO_TO_TOPIC_INTAKE_LABEL,
    GO_TO_TOPIC_SCOPE_LABEL,
    INTRO_TEXT,
    MISSING_SCOPE_MESSAGE,
    PAPER_INGESTION_STEPS,
    RELATED_PAPER_SEARCH_PAGE_KEY,
    paper_ingestion_stepper_items,
    render_paper_ingestion,
    render_paper_ingestion_header,
)
from paper_reviewer.ui.related_paper_search import render_related_paper_search


def test_render_paper_ingestion_is_public() -> None:
    assert callable(render_paper_ingestion)


def test_render_paper_ingestion_header_is_public() -> None:
    assert callable(render_paper_ingestion_header)


def test_paper_ingestion_render_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert pages["paper_ingestion"].render is render_paper_ingestion
    assert pages["paper_ingestion"].title == "Paper ingestion"
    assert pages["paper_ingestion"].url_path == "paper-ingestion"
    assert pages["paper_ingestion"].in_sidebar is False


def test_missing_key_copy_links_to_intake_and_hub() -> None:
    assert MISSING_SCOPE_MESSAGE == (
        "Open Topic intake to create a Topic scope, then open Paper ingestion from "
        "the Topic scope hub."
    )
    assert GO_TO_TOPIC_INTAKE_LABEL == "Go to Topic intake"
    assert GO_TO_TOPIC_SCOPE_LABEL == "Go to Topic scope"


def test_intro_and_primary_link_target_related_paper_search() -> None:
    assert INTRO_TEXT == (
        "This phase searches paper sources and ingests papers for this Topic scope."
    )
    assert RELATED_PAPER_SEARCH_PAGE_KEY == "related_paper_search"
    assert CONTINUE_TO_RELATED_PAPER_SEARCH_LABEL == (
        "Continue to Related-paper search"
    )


def test_paper_ingestion_steps_are_the_ingest_chain() -> None:
    assert PAPER_INGESTION_STEPS == (
        ("related_paper_search", "Related-paper search"),
        ("paper_archiving", "Paper archiving"),
        ("fulfill_papers_metadata", "Fulfill papers metadata"),
        ("generate_paper_brief", "Generate paper brief"),
    )


def test_landing_marks_no_step_current() -> None:
    items = paper_ingestion_stepper_items("paper_ingestion")

    assert [item.page_key for item in items] == [
        key for key, _label in PAPER_INGESTION_STEPS
    ]
    assert [item.step_number for item in items] == [1, 2, 3, 4]
    assert all(item.is_current is False for item in items)


def test_stepper_marks_only_the_current_step() -> None:
    items = paper_ingestion_stepper_items("paper_archiving")
    current = [item for item in items if item.is_current]

    assert len(current) == 1
    assert current[0].page_key == "paper_archiving"
    assert current[0].label == "Paper archiving"
    assert current[0].step_number == 2


def test_unknown_page_marks_no_step_current() -> None:
    items = paper_ingestion_stepper_items("topic_scope")

    assert all(item.is_current is False for item in items)


def test_current_step_badge_copy() -> None:
    assert CURRENT_STEP_BADGE == "Current"


def test_ingest_pages_render_the_phase_header() -> None:
    renders = (
        render_paper_ingestion,
        render_related_paper_search,
        render_paper_archiving,
        render_fulfill_papers_metadata,
        render_generate_paper_brief,
    )
    for render in renders:
        source = inspect.getsource(render)
        assert "render_paper_ingestion_header" in source, render.__name__
