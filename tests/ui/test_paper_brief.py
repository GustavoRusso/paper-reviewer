"""Paper brief reader page: registration, copy, caption, and sections."""

from __future__ import annotations

import inspect
from decimal import Decimal

from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    PaperBriefContent,
)
from paper_reviewer.ui import paper_brief as paper_brief_module
from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.paper_brief import (
    GO_TO_SHOW_REFERENCES_LABEL,
    INVALID_CONTENT_MESSAGE,
    MISSING_DOI_MESSAGE,
    NO_SUCCEEDED_BRIEF_MESSAGE,
    PAPER_MISSING_MESSAGE,
    format_paper_brief_caption,
    format_paper_brief_evaluation_caption,
    paper_brief_display_sections,
    render_paper_brief,
)


def test_render_paper_brief_is_public() -> None:
    assert callable(render_paper_brief)


def test_paper_brief_render_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert pages["paper_brief"].render is render_paper_brief
    assert pages["paper_brief"].title == "Paper brief"
    assert pages["paper_brief"].url_path == "paper-brief"
    assert pages["paper_brief"].in_sidebar is False


def test_empty_state_copy() -> None:
    assert MISSING_DOI_MESSAGE == (
        "Open this page from Show references to read a paper brief."
    )
    assert PAPER_MISSING_MESSAGE == "No ingested paper matches this DOI."
    assert NO_SUCCEEDED_BRIEF_MESSAGE == (
        "This paper has no succeeded paper brief yet."
    )
    assert INVALID_CONTENT_MESSAGE == (
        "Stored paper brief content could not be displayed."
    )
    assert GO_TO_SHOW_REFERENCES_LABEL == "Go to Show references"


def test_page_uses_title_not_phase_header() -> None:
    source = inspect.getsource(render_paper_brief)
    assert "st.title" in source
    assert "render_references_selection_header" not in source
    assert "st.header" not in source


def test_page_parses_doi_and_topic_scope_key() -> None:
    source = inspect.getsource(render_paper_brief)
    assert "parse_doi" in source
    assert "parse_topic_scope_key" in source
    assert "load_paper_brief_for_read" in source


def test_page_links_back_to_show_references() -> None:
    source = inspect.getsource(paper_brief_module)
    assert '"show_references"' in source
    assert "GO_TO_SHOW_REFERENCES_LABEL" in source


def test_page_renders_title_as_content_link_and_sections() -> None:
    source = inspect.getsource(paper_brief_module)
    assert "result.title" in source
    assert "result.url" in source
    assert "st.markdown" in source
    assert "paper_brief_display_sections" in source
    assert "INVALID_CONTENT_MESSAGE" in source
    assert "st.warning" in source


def test_format_paper_brief_caption() -> None:
    assert (
        format_paper_brief_caption(
            authors=["Ada Lovelace", "Alan Turing"],
            journal="Nature",
            published_year=2024,
            doi="10.1000/A",
        )
        == "Ada Lovelace, Alan Turing · Nature · 2024 · DOI `10.1000/A`"
    )


def test_format_paper_brief_caption_missing_optional_fields() -> None:
    assert (
        format_paper_brief_caption(
            authors=[],
            journal=None,
            published_year=None,
            doi="10.1000/B",
        )
        == "— · — · — · DOI `10.1000/B`"
    )


def test_format_paper_brief_evaluation_caption_shows_two_decimal_score() -> None:
    caption = format_paper_brief_evaluation_caption(Decimal("4.25"))

    assert caption == "evaluation 4.25"
    assert "faithfulness" not in caption
    assert "completeness" not in caption
    assert "conciseness" not in caption
    assert "topic_agnostic" not in caption


def test_format_paper_brief_evaluation_caption_omitted_when_score_is_null() -> None:
    assert format_paper_brief_evaluation_caption(None) is None


def test_header_shows_evaluation_score_caption_when_set() -> None:
    source = inspect.getsource(paper_brief_module)
    assert "format_paper_brief_evaluation_caption" in source
    assert "result.evaluation_score" in source
    assert "evaluation_error_message" not in source


def test_paper_brief_display_sections_skips_empty_optionals() -> None:
    content = PaperBriefContent(
        summary="Why it matters.",
        objective="Close a knowledge gap.",
        study_type="Cohort",
        key_findings=["Metric increased.", "Safety held."],
        discussion="Authors compare to prior work.",
    )

    sections = paper_brief_display_sections(content)

    assert sections[0] == ("Summary", "Why it matters.")
    assert sections[1] == ("Objective", "Close a knowledge gap.")
    assert ("Study type", "Cohort") in sections
    assert ("Key findings", ["Metric increased.", "Safety held."]) in sections
    assert ("Discussion", "Authors compare to prior work.") in sections
    labels = [label for label, _ in sections]
    assert labels.index("Summary") < labels.index("Objective")
    assert labels.index("Objective") < labels.index("Study type")
    assert labels.index("Study type") < labels.index("Key findings")
    assert labels.index("Key findings") < labels.index("Discussion")
    assert "Timeline and geography" not in labels
    assert "Population and sample" not in labels
    assert "Key methods" not in labels
    assert "Limitations" not in labels
    assert "Recommendations" not in labels
