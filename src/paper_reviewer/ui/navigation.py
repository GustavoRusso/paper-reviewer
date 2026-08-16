"""Declarative Streamlit page registry for the web UI."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AppPage:
    """One navigable page in the Streamlit app.

    ``in_sidebar`` is opt-in. Default ``False`` keeps the page registered and
    reachable but out of the left navigation chrome.
    """

    key: str
    title: str
    render: Callable[[], None]
    default: bool = False
    url_path: str | None = None
    in_sidebar: bool = False


_STREAMLIT_PAGES: dict[str, Any] = {}


def build_app_pages() -> list[AppPage]:
    """Return ordered app pages (landing first as the default entry)."""
    from paper_reviewer.ui.fulfill_papers_metadata import (
        render_fulfill_papers_metadata,
    )
    from paper_reviewer.ui.generate_paper_brief import render_generate_paper_brief
    from paper_reviewer.ui.landing import render_landing
    from paper_reviewer.ui.paper_archiving import render_paper_archiving
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

    return [
        AppPage(
            key="landing",
            title="Home",
            render=render_landing,
            default=True,
            in_sidebar=True,
        ),
        AppPage(
            key="topic_intake",
            title="Topic intake",
            render=render_topic_intake,
            url_path="topic-intake",
            in_sidebar=True,
        ),
        AppPage(
            key="topic_analysis",
            title="Topic analysis",
            render=render_topic_analysis,
            url_path="topic-analysis",
        ),
        AppPage(
            key="topic_scope",
            title="Topic scope",
            render=render_topic_scope,
            url_path="topic-scope",
        ),
        AppPage(
            key="external_sources_ingestion",
            title="External sources ingestion",
            render=render_external_sources_ingestion,
            url_path="external-sources-ingestion",
        ),
        AppPage(
            key="show_references",
            title="Show references",
            render=render_show_references,
            url_path="show-references",
        ),
        AppPage(
            key="add_reference",
            title="Add reference",
            render=render_add_reference,
            url_path="add-reference",
        ),
        AppPage(
            key="topic_brief_generation",
            title="Topic brief generation",
            render=render_topic_brief_generation,
            url_path="topic-brief-generation",
        ),
        AppPage(
            key="search_external_sources",
            title="Search external sources",
            render=render_search_external_sources,
            url_path="search-external-sources",
        ),
        AppPage(
            key="paper_archiving",
            title="Paper archiving",
            render=render_paper_archiving,
            url_path="paper-archiving",
        ),
        AppPage(
            key="fulfill_papers_metadata",
            title="Fulfill papers metadata",
            render=render_fulfill_papers_metadata,
            url_path="fulfill-papers-metadata",
        ),
        AppPage(
            key="generate_paper_brief",
            title="Generate paper brief",
            render=render_generate_paper_brief,
            url_path="generate-paper-brief",
        ),
    ]


def page_by_key(key: str) -> AppPage:
    """Look up a registered page definition by key."""
    for page in build_app_pages():
        if page.key == key:
            return page
    raise KeyError(f"unknown app page: {key}")


def bind_streamlit_pages(pages: dict[str, Any]) -> None:
    """Store Streamlit ``st.Page`` objects for ``st.page_link`` targets."""
    _STREAMLIT_PAGES.clear()
    _STREAMLIT_PAGES.update(pages)


def streamlit_page_for(key: str) -> Any:
    """Return the bound Streamlit page for ``key`` (set by the app entry)."""
    try:
        return _STREAMLIT_PAGES[key]
    except KeyError as exc:
        raise KeyError(f"streamlit page not bound: {key}") from exc
