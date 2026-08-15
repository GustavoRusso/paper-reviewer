"""Topic analysis page: registration and public render name."""

from __future__ import annotations

from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.topic_analysis import render_topic_analysis


def test_render_topic_analysis_is_public() -> None:
    assert callable(render_topic_analysis)


def test_topic_analysis_render_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert pages["topic_analysis"].render is render_topic_analysis
