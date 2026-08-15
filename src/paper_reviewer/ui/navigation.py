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
    from paper_reviewer.ui.paper_ingestion import render_paper_ingestion
    from paper_reviewer.ui.paper_search import render_paper_search
    from paper_reviewer.ui.related_paper_search import render_related_paper_search
    from paper_reviewer.ui.retrieval_triage import render_retrieval_triage
    from paper_reviewer.ui.topic_analysis import render_topic_analysis
    from paper_reviewer.ui.topic_brief import render_topic_brief
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
            key="paper_ingestion",
            title="Paper ingestion",
            render=render_paper_ingestion,
            url_path="paper-ingestion",
        ),
        AppPage(
            key="paper_search",
            title="Paper search",
            render=render_paper_search,
            url_path="paper-search",
        ),
        AppPage(
            key="topic_brief",
            title="Topic brief",
            render=render_topic_brief,
            url_path="topic-brief",
        ),
        AppPage(
            key="related_paper_search",
            title="Related-paper search",
            render=render_related_paper_search,
            url_path="related-paper-search",
        ),
        AppPage(
            key="retrieval_triage",
            title="Retrieval triage",
            render=render_retrieval_triage,
            url_path="retrieval-triage",
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
