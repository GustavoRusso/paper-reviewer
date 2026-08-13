"""Declarative Streamlit page registry for the web UI."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AppPage:
    """One navigable page in the Streamlit app."""

    key: str
    title: str
    render: Callable[[], None]
    default: bool = False
    url_path: str | None = None


_STREAMLIT_PAGES: dict[str, Any] = {}


def build_app_pages() -> list[AppPage]:
    """Return ordered app pages (landing first as the default entry)."""
    from paper_reviewer.ui.fulfill_papers_metadata import (
        render_fulfill_papers_metadata,
    )
    from paper_reviewer.ui.generate_paper_brief import render_generate_paper_brief
    from paper_reviewer.ui.landing import render_landing
    from paper_reviewer.ui.paper_archiving import render_paper_archiving
    from paper_reviewer.ui.retrieval_triage import render_retrieval_triage
    from paper_reviewer.ui.topic_intake import render_topic_intake

    return [
        AppPage(
            key="landing",
            title="Home",
            render=render_landing,
            default=True,
        ),
        AppPage(
            key="new_topic_brief",
            title="New Topic brief",
            render=render_topic_intake,
            url_path="new-topic-brief",
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
