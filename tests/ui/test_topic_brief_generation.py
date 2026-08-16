"""Topic brief generation landing: registration, gate helpers, and copy."""

from __future__ import annotations

from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.topic_brief_generation import (
    GENERATE_TOPIC_BRIEF_LABEL,
    GO_TO_GENERATE_PAPER_BRIEF_LABEL,
    GO_TO_SHOW_REFERENCES_LABEL,
    GO_TO_TOPIC_INTAKE_LABEL,
    GO_TO_TOPIC_SCOPE_LABEL,
    MISSING_SCOPE_MESSAGE,
    ZERO_BRIEFED_CAPTION,
    generate_button_enabled,
    render_topic_brief_generation,
)


def test_render_topic_brief_generation_is_public() -> None:
    assert callable(render_topic_brief_generation)


def test_topic_brief_generation_render_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert pages["topic_brief_generation"].render is render_topic_brief_generation
    assert pages["topic_brief_generation"].title == "Topic brief generation"
    assert pages["topic_brief_generation"].url_path == "topic-brief-generation"
    assert pages["topic_brief_generation"].in_sidebar is False


def test_missing_key_copy_links_to_intake_and_hub() -> None:
    assert MISSING_SCOPE_MESSAGE == (
        "Open Topic intake to create a Topic scope, then open Topic brief "
        "generation from the Topic scope hub."
    )
    assert GO_TO_TOPIC_INTAKE_LABEL == "Go to Topic intake"
    assert GO_TO_TOPIC_SCOPE_LABEL == "Go to Topic scope"


def test_zero_briefed_caption_and_helpful_links() -> None:
    assert ZERO_BRIEFED_CAPTION == (
        "Generation needs at least one Reference with a succeeded paper brief."
    )
    assert GO_TO_SHOW_REFERENCES_LABEL == "Go to Show references"
    assert GO_TO_GENERATE_PAPER_BRIEF_LABEL == "Go to Generate paper brief"


def test_generate_button_label() -> None:
    assert GENERATE_TOPIC_BRIEF_LABEL == "Generate topic brief"


def test_generate_button_disabled_when_zero_briefed() -> None:
    assert generate_button_enabled(briefed_count=0) is False


def test_generate_button_enabled_when_at_least_one_briefed() -> None:
    assert generate_button_enabled(briefed_count=1) is True
    assert generate_button_enabled(briefed_count=3) is True
