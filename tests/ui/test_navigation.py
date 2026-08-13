"""App navigation: landing page and New Topic brief entry."""

from __future__ import annotations

from paper_reviewer.ui.fulfill_papers_metadata import render_fulfill_papers_metadata
from paper_reviewer.ui.landing import LANDING_CTA_LABEL, landing_cta_page_key
from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.paper_archiving import render_paper_archiving
from paper_reviewer.ui.retrieval_triage import render_retrieval_triage
from paper_reviewer.ui.topic_intake import render_topic_intake


def test_landing_is_the_default_page() -> None:
    pages = build_app_pages()
    defaults = [page for page in pages if page.default]

    assert len(defaults) == 1
    assert defaults[0].key == "landing"


def test_new_topic_brief_page_uses_topic_intake() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "new_topic_brief" in pages
    assert pages["new_topic_brief"].title == "New Topic brief"
    assert pages["new_topic_brief"].render is render_topic_intake


def test_retrieval_triage_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "retrieval_triage" in pages
    assert pages["retrieval_triage"].title == "Retrieval triage"
    assert pages["retrieval_triage"].url_path == "retrieval-triage"
    assert pages["retrieval_triage"].render is render_retrieval_triage


def test_paper_archiving_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "paper_archiving" in pages
    assert pages["paper_archiving"].title == "Paper archiving"
    assert pages["paper_archiving"].url_path == "paper-archiving"
    assert pages["paper_archiving"].render is render_paper_archiving


def test_fulfill_papers_metadata_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "fulfill_papers_metadata" in pages
    assert pages["fulfill_papers_metadata"].title == "Fulfill papers metadata"
    assert pages["fulfill_papers_metadata"].url_path == "fulfill-papers-metadata"
    assert pages["fulfill_papers_metadata"].render is render_fulfill_papers_metadata


def test_workflow_page_order() -> None:
    keys = [page.key for page in build_app_pages()]

    assert keys.index("new_topic_brief") < keys.index("retrieval_triage")
    assert keys.index("retrieval_triage") < keys.index("paper_archiving")
    assert keys.index("paper_archiving") < keys.index("fulfill_papers_metadata")


def test_landing_cta_links_to_new_topic_brief() -> None:
    assert LANDING_CTA_LABEL == "Go to New Topic brief"
    assert landing_cta_page_key() == "new_topic_brief"
