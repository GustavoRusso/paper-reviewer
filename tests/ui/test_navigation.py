"""App navigation: landing page and Topic intake entry."""

from __future__ import annotations

from paper_reviewer.ui.landing import LANDING_CTA_LABEL, landing_cta_page_key
from paper_reviewer.ui.navigation import AppPage, build_app_pages
from paper_reviewer.ui.paper_archiving import render_paper_archiving
from paper_reviewer.ui.paper_brief import render_paper_brief
from paper_reviewer.ui.external_sources_ingestion import (
    render_external_sources_ingestion,
)
from paper_reviewer.ui.add_reference import render_add_reference
from paper_reviewer.ui.search_external_sources import render_search_external_sources
from paper_reviewer.ui.show_references import render_show_references
from paper_reviewer.ui.topic_analysis import render_topic_analysis
from paper_reviewer.ui.topic_brief_generation import render_topic_brief_generation
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


def test_external_sources_ingestion_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "external_sources_ingestion" in pages
    assert pages["external_sources_ingestion"].title == "External sources ingestion"
    assert pages["external_sources_ingestion"].url_path == "external-sources-ingestion"
    assert pages["external_sources_ingestion"].render is (
        render_external_sources_ingestion
    )
    assert pages["external_sources_ingestion"].in_sidebar is False


def test_references_selection_page_is_not_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "references_selection" not in pages


def test_show_references_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "show_references" in pages
    assert pages["show_references"].title == "Show references"
    assert pages["show_references"].url_path == "show-references"
    assert pages["show_references"].render is render_show_references
    assert pages["show_references"].in_sidebar is False


def test_add_reference_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "add_reference" in pages
    assert pages["add_reference"].title == "Add reference"
    assert pages["add_reference"].url_path == "add-reference"
    assert pages["add_reference"].render is render_add_reference
    assert pages["add_reference"].in_sidebar is False


def test_paper_search_page_is_not_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "paper_search" not in pages


def test_topic_brief_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "topic_brief_generation" in pages
    assert pages["topic_brief_generation"].title == "Topic brief generation"
    assert pages["topic_brief_generation"].url_path == "topic-brief-generation"
    assert pages["topic_brief_generation"].render is render_topic_brief_generation
    assert pages["topic_brief_generation"].in_sidebar is False


def test_search_external_sources_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "search_external_sources" in pages
    assert pages["search_external_sources"].title == "Search external sources"
    assert pages["search_external_sources"].url_path == "search-external-sources"
    assert pages["search_external_sources"].render is render_search_external_sources
    assert pages["search_external_sources"].in_sidebar is False


def test_retrieval_triage_page_is_not_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "retrieval_triage" not in pages


def test_paper_archiving_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "paper_archiving" in pages
    assert pages["paper_archiving"].title == "Paper archiving"
    assert pages["paper_archiving"].url_path == "paper-archiving"
    assert pages["paper_archiving"].render is render_paper_archiving


def test_fulfill_papers_metadata_page_is_not_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "fulfill_papers_metadata" not in pages


def test_paper_brief_page_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "paper_brief" in pages
    assert pages["paper_brief"].title == "Paper brief"
    assert pages["paper_brief"].url_path == "paper-brief"
    assert pages["paper_brief"].render is render_paper_brief
    assert pages["paper_brief"].in_sidebar is False


def test_generate_paper_brief_page_is_not_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert "generate_paper_brief" not in pages


def test_workflow_page_order() -> None:
    keys = [page.key for page in build_app_pages()]

    assert keys.index("topic_intake") < keys.index("topic_analysis")
    assert keys.index("topic_analysis") < keys.index("topic_scope")
    assert keys.index("topic_scope") < keys.index("external_sources_ingestion")
    assert keys.index("external_sources_ingestion") < keys.index("show_references")
    assert keys.index("show_references") < keys.index("paper_brief")
    assert keys.index("paper_brief") < keys.index("add_reference")
    assert keys.index("show_references") < keys.index("add_reference")
    assert keys.index("add_reference") < keys.index("topic_brief_generation")
    assert keys.index("external_sources_ingestion") < keys.index(
        "search_external_sources"
    )
    assert keys.index("search_external_sources") < keys.index("paper_archiving")


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
    assert by_key["external_sources_ingestion"].in_sidebar is False
    assert by_key["show_references"].in_sidebar is False
    assert by_key["paper_brief"].in_sidebar is False
    assert by_key["add_reference"].in_sidebar is False
    assert by_key["topic_brief_generation"].in_sidebar is False
    assert by_key["search_external_sources"].in_sidebar is False
    assert by_key["paper_archiving"].in_sidebar is False
