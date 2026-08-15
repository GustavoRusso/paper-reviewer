"""Topic scope hub: registration, public render name, and view states."""

from __future__ import annotations

from uuid import uuid4

from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.topic_scope import (
    CONTINUE_TO_EXTERNAL_SOURCES_INGESTION_LABEL,
    CONTINUE_TO_PAPER_SEARCH_LABEL,
    CONTINUE_TO_TOPIC_BRIEF_LABEL,
    GO_TO_TOPIC_ANALYSIS_LABEL,
    GO_TO_TOPIC_INTAKE_LABEL,
    INCOMPLETE_MESSAGE,
    MISSING_SCOPE_MESSAGE,
    PHASE_LANDING_PAGE_KEYS,
    render_topic_scope,
    topic_scope_hub_view,
)


def test_render_topic_scope_is_public() -> None:
    assert callable(render_topic_scope)


def test_topic_scope_render_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert pages["topic_scope"].render is render_topic_scope
    assert pages["topic_scope"].title == "Topic scope"
    assert pages["topic_scope"].url_path == "topic-scope"
    assert pages["topic_scope"].in_sidebar is False


def test_hub_view_is_missing_when_key_is_absent() -> None:
    assert (
        topic_scope_hub_view(
            topic_scope_key=None,
            has_scope=False,
            has_facets=False,
        )
        == "missing_scope"
    )


def test_hub_view_is_missing_when_scope_row_is_absent() -> None:
    assert (
        topic_scope_hub_view(
            topic_scope_key=uuid4(),
            has_scope=False,
            has_facets=False,
        )
        == "missing_scope"
    )


def test_hub_view_is_incomplete_when_scope_has_no_facets() -> None:
    assert (
        topic_scope_hub_view(
            topic_scope_key=uuid4(),
            has_scope=True,
            has_facets=False,
        )
        == "incomplete"
    )


def test_hub_view_is_ready_when_facets_exist() -> None:
    assert (
        topic_scope_hub_view(
            topic_scope_key=uuid4(),
            has_scope=True,
            has_facets=True,
        )
        == "ready"
    )


def test_missing_scope_copy_and_intake_link_label() -> None:
    assert MISSING_SCOPE_MESSAGE == (
        "Open Topic intake to create a Topic scope, then open it here."
    )
    assert GO_TO_TOPIC_INTAKE_LABEL == "Go to Topic intake"


def test_incomplete_copy_and_analysis_link_label() -> None:
    assert INCOMPLETE_MESSAGE == (
        "This Topic scope has no topic facets yet. "
        "Open Topic analysis to extract them."
    )
    assert GO_TO_TOPIC_ANALYSIS_LABEL == "Go to Topic analysis"


def test_ready_hub_links_to_the_three_phase_landings() -> None:
    assert PHASE_LANDING_PAGE_KEYS == (
        "external_sources_ingestion",
        "paper_search",
        "topic_brief",
    )
    assert CONTINUE_TO_EXTERNAL_SOURCES_INGESTION_LABEL == (
        "Continue to External sources ingestion"
    )
    assert CONTINUE_TO_PAPER_SEARCH_LABEL == "Continue to Paper search"
    assert CONTINUE_TO_TOPIC_BRIEF_LABEL == "Continue to Topic brief"
