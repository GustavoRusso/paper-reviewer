"""Topic brief generation landing: registration, public render name, and copy."""

from __future__ import annotations

from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.topic_brief_generation import (
    GO_TO_TOPIC_INTAKE_LABEL,
    GO_TO_TOPIC_SCOPE_LABEL,
    MISSING_SCOPE_MESSAGE,
    NOT_BUILT_CAPTION,
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


def test_not_built_caption() -> None:
    assert NOT_BUILT_CAPTION == (
        "Drafting the cited topic brief is not built yet."
    )
