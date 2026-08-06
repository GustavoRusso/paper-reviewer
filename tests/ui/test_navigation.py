"""App navigation: landing page and New Topic brief entry."""

from __future__ import annotations

from paper_reviewer.ui.landing import LANDING_CTA_LABEL, landing_cta_page_key
from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.query_intake import render_query_intake


def test_landing_is_the_default_page() -> None:
    pages = build_app_pages()
    defaults = [page for page in pages if page.default]

    assert len(defaults) == 1
    assert defaults[0].key == "landing"


def test_new_topic_brief_page_uses_query_intake() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "new_topic_brief" in pages
    assert pages["new_topic_brief"].title == "New Topic brief"
    assert pages["new_topic_brief"].render is render_query_intake


def test_landing_cta_links_to_new_topic_brief() -> None:
    assert LANDING_CTA_LABEL == "Create a new Topic brief"
    assert landing_cta_page_key() == "new_topic_brief"
