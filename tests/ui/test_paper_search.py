"""Paper search landing: registration, public render name, and copy."""

from __future__ import annotations

from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.paper_search import (
    GO_TO_TOPIC_INTAKE_LABEL,
    GO_TO_TOPIC_SCOPE_LABEL,
    MISSING_SCOPE_MESSAGE,
    NOT_BUILT_CAPTION,
    render_paper_search,
)


def test_render_paper_search_is_public() -> None:
    assert callable(render_paper_search)


def test_paper_search_render_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert pages["paper_search"].render is render_paper_search
    assert pages["paper_search"].title == "Paper search"
    assert pages["paper_search"].url_path == "paper-search"
    assert pages["paper_search"].in_sidebar is False


def test_missing_key_copy_links_to_intake_and_hub() -> None:
    assert MISSING_SCOPE_MESSAGE == (
        "Open Topic intake to create a Topic scope, then open Paper search from "
        "the Topic scope hub."
    )
    assert GO_TO_TOPIC_INTAKE_LABEL == "Go to Topic intake"
    assert GO_TO_TOPIC_SCOPE_LABEL == "Go to Topic scope"


def test_not_built_caption() -> None:
    assert NOT_BUILT_CAPTION == (
        "Search of locally ingested papers is not built yet."
    )
