"""Topic scope hub: registration, public render name, and view states."""

from __future__ import annotations

from uuid import uuid4

from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.topic_scope import (
    GO_TO_TOPIC_ANALYSIS_LABEL,
    GO_TO_TOPIC_INTAKE_LABEL,
    HUB_ACTIONS_TITLE,
    HUB_EXTERNAL_SOURCES_INGESTION_LABEL,
    HUB_EXTERNAL_SOURCES_INGESTION_PAGE_KEY,
    HUB_REFERENCES_PAGE_KEY,
    HUB_REFERENCES_TITLE,
    HUB_TOPIC_BRIEF_LABEL,
    HUB_TOPIC_BRIEF_PAGE_KEY,
    HUB_TOPIC_BRIEF_TITLE,
    INCOMPLETE_MESSAGE,
    MISSING_SCOPE_MESSAGE,
    format_hub_reference_count_label,
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


def test_ready_hub_action_row_pane_titles() -> None:
    assert HUB_REFERENCES_TITLE == "References"
    assert HUB_TOPIC_BRIEF_TITLE == "Topic Brief"
    assert HUB_ACTIONS_TITLE == "Actions"


def test_ready_hub_action_row_destinations() -> None:
    assert HUB_REFERENCES_PAGE_KEY == "show_references"
    assert HUB_TOPIC_BRIEF_PAGE_KEY == "topic_brief_generation"
    assert HUB_EXTERNAL_SOURCES_INGESTION_PAGE_KEY == (
        "external_sources_ingestion"
    )
    assert HUB_TOPIC_BRIEF_LABEL == "Topic brief generation"
    assert HUB_EXTERNAL_SOURCES_INGESTION_LABEL == (
        "External sources ingestion"
    )


def test_hub_reference_count_label_is_the_decimal_count() -> None:
    assert format_hub_reference_count_label(0) == "0"
    assert format_hub_reference_count_label(3) == "3"
