"""Streamlit app entry — landing page and Topic scope workflow."""

from __future__ import annotations

import streamlit as st

from paper_reviewer.ui.navigation import bind_streamlit_pages, build_app_pages


def main() -> None:
    """Configure multipage navigation and run the selected page."""
    st.set_page_config(
        page_title="Paper Reviewer",
        page_icon=None,
        layout="centered",
    )

    definitions = build_app_pages()
    streamlit_pages: dict[str, st.Page] = {}
    ordered: list[st.Page] = []
    for definition in definitions:
        page_kwargs: dict[str, object] = {
            "title": definition.title,
            "default": definition.default,
            "visibility": "visible" if definition.in_sidebar else "hidden",
        }
        if definition.url_path is not None:
            page_kwargs["url_path"] = definition.url_path
        page = st.Page(definition.render, **page_kwargs)
        streamlit_pages[definition.key] = page
        ordered.append(page)

    bind_streamlit_pages(streamlit_pages)
    st.navigation(ordered).run()


main()
