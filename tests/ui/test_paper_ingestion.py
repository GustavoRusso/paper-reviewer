"""Paper ingestion landing: registration, public render name, and copy."""

from __future__ import annotations

from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.paper_ingestion import (
    CONTINUE_TO_FULFILL_PAPERS_METADATA_LABEL,
    CONTINUE_TO_GENERATE_PAPER_BRIEF_LABEL,
    CONTINUE_TO_PAPER_ARCHIVING_LABEL,
    CONTINUE_TO_RELATED_PAPER_SEARCH_LABEL,
    GO_TO_TOPIC_INTAKE_LABEL,
    GO_TO_TOPIC_SCOPE_LABEL,
    INTRO_TEXT,
    MISSING_SCOPE_MESSAGE,
    RELATED_PAPER_SEARCH_PAGE_KEY,
    render_paper_ingestion,
)


def test_render_paper_ingestion_is_public() -> None:
    assert callable(render_paper_ingestion)


def test_paper_ingestion_render_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert pages["paper_ingestion"].render is render_paper_ingestion
    assert pages["paper_ingestion"].title == "Paper ingestion"
    assert pages["paper_ingestion"].url_path == "paper-ingestion"
    assert pages["paper_ingestion"].in_sidebar is False


def test_missing_key_copy_links_to_intake_and_hub() -> None:
    assert MISSING_SCOPE_MESSAGE == (
        "Open Topic intake to create a Topic scope, then open Paper ingestion from "
        "the Topic scope hub."
    )
    assert GO_TO_TOPIC_INTAKE_LABEL == "Go to Topic intake"
    assert GO_TO_TOPIC_SCOPE_LABEL == "Go to Topic scope"


def test_intro_and_primary_link_target_related_paper_search() -> None:
    assert INTRO_TEXT == (
        "This phase searches paper sources and ingests papers for this Topic scope."
    )
    assert RELATED_PAPER_SEARCH_PAGE_KEY == "related_paper_search"
    assert CONTINUE_TO_RELATED_PAPER_SEARCH_LABEL == (
        "Continue to Related-paper search"
    )


def test_optional_further_ingest_link_labels() -> None:
    assert CONTINUE_TO_PAPER_ARCHIVING_LABEL == "Continue to Paper archiving"
    assert CONTINUE_TO_FULFILL_PAPERS_METADATA_LABEL == (
        "Continue to Fulfill papers metadata"
    )
    assert CONTINUE_TO_GENERATE_PAPER_BRIEF_LABEL == (
        "Continue to Generate paper brief"
    )
