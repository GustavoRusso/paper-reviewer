"""Related-paper search page stub: registration and public render name."""

from __future__ import annotations

from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.related_paper_search import render_related_paper_search


def test_render_related_paper_search_is_public() -> None:
    assert callable(render_related_paper_search)


def test_related_paper_search_render_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert pages["related_paper_search"].render is render_related_paper_search
    assert pages["related_paper_search"].title == "Related-paper search"
    assert pages["related_paper_search"].url_path == "related-paper-search"
    assert pages["related_paper_search"].in_sidebar is False
