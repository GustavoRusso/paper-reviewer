"""App navigation: landing page and Topic intake entry."""

from __future__ import annotations

from paper_reviewer.ui.fulfill_papers_metadata import render_fulfill_papers_metadata
from paper_reviewer.ui.generate_paper_brief import render_generate_paper_brief
from paper_reviewer.ui.landing import LANDING_CTA_LABEL, landing_cta_page_key
from paper_reviewer.ui.navigation import AppPage, build_app_pages
from paper_reviewer.ui.paper_archiving import render_paper_archiving
from paper_reviewer.ui.paper_ingestion import render_paper_ingestion
from paper_reviewer.ui.paper_search import render_paper_search
from paper_reviewer.ui.related_paper_search import render_related_paper_search
from paper_reviewer.ui.retrieval_triage import render_retrieval_triage
from paper_reviewer.ui.topic_analysis import render_topic_analysis
from paper_reviewer.ui.topic_brief import render_topic_brief
from paper_reviewer.ui.topic_intake import render_topic_intake
from paper_reviewer.ui.topic_scope import render_topic_scope


def test_landing_is_the_default_page() -> None:
    pages = build_app_pages()
    defaults = [page for page in pages if page.default]

    assert len(defaults) == 1
    assert defaults[0].key == "landing"


def test_topic_intake_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "topic_intake" in pages
    assert pages["topic_intake"].title == "Topic intake"
    assert pages["topic_intake"].url_path == "topic-intake"
    assert pages["topic_intake"].render is render_topic_intake
    assert pages["topic_intake"].in_sidebar is True


def test_new_topic_brief_page_is_not_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "new_topic_brief" not in pages


def test_topic_analysis_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "topic_analysis" in pages
    assert pages["topic_analysis"].title == "Topic analysis"
    assert pages["topic_analysis"].url_path == "topic-analysis"
    assert pages["topic_analysis"].render is render_topic_analysis
    assert pages["topic_analysis"].in_sidebar is False


def test_topic_scope_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "topic_scope" in pages
    assert pages["topic_scope"].title == "Topic scope"
    assert pages["topic_scope"].url_path == "topic-scope"
    assert pages["topic_scope"].render is render_topic_scope
    assert pages["topic_scope"].in_sidebar is False


def test_paper_ingestion_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "paper_ingestion" in pages
    assert pages["paper_ingestion"].title == "Paper ingestion"
    assert pages["paper_ingestion"].url_path == "paper-ingestion"
    assert pages["paper_ingestion"].render is render_paper_ingestion
    assert pages["paper_ingestion"].in_sidebar is False


def test_paper_search_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "paper_search" in pages
    assert pages["paper_search"].title == "Paper search"
    assert pages["paper_search"].url_path == "paper-search"
    assert pages["paper_search"].render is render_paper_search
    assert pages["paper_search"].in_sidebar is False


def test_topic_brief_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "topic_brief" in pages
    assert pages["topic_brief"].title == "Topic brief"
    assert pages["topic_brief"].url_path == "topic-brief"
    assert pages["topic_brief"].render is render_topic_brief
    assert pages["topic_brief"].in_sidebar is False


def test_related_paper_search_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "related_paper_search" in pages
    assert pages["related_paper_search"].title == "Related-paper search"
    assert pages["related_paper_search"].url_path == "related-paper-search"
    assert pages["related_paper_search"].render is render_related_paper_search
    assert pages["related_paper_search"].in_sidebar is False


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


def test_generate_paper_brief_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "generate_paper_brief" in pages
    assert pages["generate_paper_brief"].title == "Generate paper brief"
    assert pages["generate_paper_brief"].url_path == "generate-paper-brief"
    assert pages["generate_paper_brief"].render is render_generate_paper_brief


def test_workflow_page_order() -> None:
    keys = [page.key for page in build_app_pages()]

    assert keys.index("topic_intake") < keys.index("topic_analysis")
    assert keys.index("topic_analysis") < keys.index("topic_scope")
    assert keys.index("topic_scope") < keys.index("paper_ingestion")
    assert keys.index("paper_ingestion") < keys.index("paper_search")
    assert keys.index("paper_search") < keys.index("topic_brief")
    assert keys.index("paper_ingestion") < keys.index("related_paper_search")
    assert keys.index("related_paper_search") < keys.index("retrieval_triage")
    assert keys.index("retrieval_triage") < keys.index("paper_archiving")
    assert keys.index("paper_archiving") < keys.index("fulfill_papers_metadata")
    assert keys.index("fulfill_papers_metadata") < keys.index("generate_paper_brief")


def test_landing_cta_links_to_topic_intake() -> None:
    assert LANDING_CTA_LABEL == "Add a Topic scope"
    assert landing_cta_page_key() == "topic_intake"


def test_app_page_in_sidebar_defaults_to_false() -> None:
    page = AppPage(key="example", title="Example", render=lambda: None)

    assert page.in_sidebar is False


def test_only_home_and_topic_intake_are_in_the_sidebar() -> None:
    pages = build_app_pages()
    sidebar_keys = [page.key for page in pages if page.in_sidebar]
    by_key = {page.key: page for page in pages}

    assert sidebar_keys == ["landing", "topic_intake"]
    assert by_key["landing"].in_sidebar is True
    assert by_key["topic_intake"].in_sidebar is True
    assert by_key["topic_analysis"].in_sidebar is False
    assert by_key["topic_scope"].in_sidebar is False
    assert by_key["paper_ingestion"].in_sidebar is False
    assert by_key["paper_search"].in_sidebar is False
    assert by_key["topic_brief"].in_sidebar is False
    assert by_key["related_paper_search"].in_sidebar is False
    assert by_key["retrieval_triage"].in_sidebar is False
    assert by_key["paper_archiving"].in_sidebar is False
    assert by_key["fulfill_papers_metadata"].in_sidebar is False
    assert by_key["generate_paper_brief"].in_sidebar is False
