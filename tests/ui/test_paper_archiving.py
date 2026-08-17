"""Paper archiving page helpers: prerequisites and display formatting."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from paper_reviewer.flows.serve import REGENERATE_PAPER_DEPLOYMENT_REF
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.paper_archiving import (
    ArchiveError,
    ArchiveSkip,
    ArchiveSkipReason,
    Paper,
    PaperArchivingResult,
)
from paper_reviewer.schemas.topic_scope.search_external_sources import (
    SearchExternalSourcesResult,
)
from paper_reviewer.ui.paper_archiving import (
    GO_TO_TOPIC_SCOPE_LABEL,
    REGENERATE_BUTTON_LABEL,
    archive_skip_reason_label,
    archiving_prerequisites_met,
    aspect_status_label,
    brief_progress_label,
    enrichment_links_caption,
    format_archived_paper_caption,
    format_brief_progress_caption,
    format_paper_archiving_summary,
    may_submit_regenerate_paper,
    paper_ingest_row_is_terminal,
    prefect_enqueue_error_hint,
    split_brief_error_message,
)
from paper_reviewer.ui.topic_intake import (
    PAPER_INGEST_ENQUEUE_RESULT_KEY,
    SEARCH_KEY,
    SEARCH_TOPIC_SCOPE_KEY,
)


def test_prerequisites_met_when_search_cache_matches() -> None:
    topic_scope_key = uuid4()
    state = {
        SEARCH_KEY: SearchExternalSourcesResult(candidates=[], source_runs=[]),
        SEARCH_TOPIC_SCOPE_KEY: str(topic_scope_key),
    }

    assert archiving_prerequisites_met(state, topic_scope_key=topic_scope_key) is True


def test_prerequisites_missing_without_search_result() -> None:
    assert archiving_prerequisites_met({}, topic_scope_key=uuid4()) is False


def test_prerequisites_missing_when_topic_scope_key_mismatches() -> None:
    state = {
        SEARCH_KEY: SearchExternalSourcesResult(candidates=[], source_runs=[]),
        SEARCH_TOPIC_SCOPE_KEY: str(uuid4()),
    }

    assert archiving_prerequisites_met(state, topic_scope_key=uuid4()) is False


def test_archive_skip_reason_labels() -> None:
    assert archive_skip_reason_label(ArchiveSkipReason.missing_doi) == "Missing DOI"
    assert (
        archive_skip_reason_label(ArchiveSkipReason.invalid_required_field)
        == "Invalid required field"
    )
    assert archive_skip_reason_label(ArchiveSkipReason.doi_conflict) == "DOI conflict"


def test_format_archived_paper_caption() -> None:
    paper = Paper(
        id=1,
        created_at=datetime(2026, 8, 11, 12, 0, 0, tzinfo=UTC),
        doi="10.1000/A",
        source_id="pubmed",
        source_uid="123",
        title="Example",
        authors=["Ada Lovelace", "Alan Turing"],
        journal="Nature",
        published_year=2024,
        url="https://example.com/1",
    )

    assert format_archived_paper_caption(paper) == (
        "Ada Lovelace, Alan Turing · Nature · 2024 · DOI `10.1000/A` · "
        "`pubmed` / `123` · 2026-08-11T12:00:00+00:00"
    )


def test_format_archived_paper_caption_missing_optional_fields() -> None:
    paper = Paper(
        id=1,
        created_at=datetime(2026, 8, 11, 12, 0, 0, tzinfo=UTC),
        doi="10.1000/B",
        source_id="pubmed",
        source_uid="456",
        title="Example",
        url="https://example.com/2",
    )

    assert format_archived_paper_caption(paper) == (
        "— · — · — · DOI `10.1000/B` · "
        "`pubmed` / `456` · 2026-08-11T12:00:00+00:00"
    )


def test_format_summary_empty_success() -> None:
    result = PaperArchivingResult(papers=[], skipped=[], errors=[])

    assert format_paper_archiving_summary(result) == (
        "Paper archiving finished: 0 paper(s), 0 skipped, 0 error(s)."
    )


def test_format_summary_reports_counts() -> None:
    now = datetime.now(UTC)
    result = PaperArchivingResult(
        papers=[
            Paper(
                id=1,
                created_at=now,
                doi="10.1000/A",
                source_id="pubmed",
                source_uid="1",
                title="A",
                url="https://example.com/1",
            ),
            Paper(
                id=2,
                created_at=now,
                doi="10.1000/B",
                source_id="pubmed",
                source_uid="2",
                title="B",
                url="https://example.com/2",
            ),
        ],
        skipped=[
            ArchiveSkip(
                reason=ArchiveSkipReason.missing_doi,
                source_id="pubmed",
                source_uid="3",
            )
        ],
        errors=[
            ArchiveError(
                reason="db failure",
                source_id="pubmed",
                source_uid="4",
            )
        ],
    )

    assert format_paper_archiving_summary(result) == (
        "Paper archiving finished: 2 paper(s), 1 skipped, 1 error(s)."
    )


def test_paper_ingest_enqueue_result_key_constant() -> None:
    assert PAPER_INGEST_ENQUEUE_RESULT_KEY == "paper_ingest_enqueue_result"


def test_go_to_topic_scope_label() -> None:
    assert GO_TO_TOPIC_SCOPE_LABEL == "Go to Topic scope"


def test_aspect_status_label_succeeded() -> None:
    assert (
        aspect_status_label(
            status=PaperAspectStatus.succeeded,
            skipped_already_succeeded=False,
        )
        == "Succeeded"
    )


def test_aspect_status_label_skipped_already_done() -> None:
    assert (
        aspect_status_label(
            status=PaperAspectStatus.succeeded,
            skipped_already_succeeded=True,
        )
        == "Skipped (already done)"
    )


def test_aspect_status_label_failed() -> None:
    assert (
        aspect_status_label(
            status=PaperAspectStatus.failed,
            skipped_already_succeeded=False,
        )
        == "Failed"
    )


def test_aspect_status_label_unavailable() -> None:
    assert (
        aspect_status_label(
            status=PaperAspectStatus.unavailable,
            skipped_already_succeeded=False,
        )
        == "Unavailable"
    )


def test_aspect_status_label_unavailable_is_not_skipped() -> None:
    assert (
        aspect_status_label(
            status=PaperAspectStatus.unavailable,
            skipped_already_succeeded=True,
        )
        == "Unavailable"
    )


def test_aspect_status_label_fulfilling() -> None:
    assert (
        aspect_status_label(
            status=PaperAspectStatus.not_started,
            skipped_already_succeeded=False,
        )
        == "Fulfilling"
    )


def test_enrichment_links_caption_empty_when_no_urls() -> None:
    assert enrichment_links_caption(None, None) is None
    assert enrichment_links_caption("", "") is None


def test_enrichment_links_caption_pmc_only() -> None:
    caption = enrichment_links_caption(
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC5334499/",
        None,
    )

    assert caption == (
        "[PMC article](https://pmc.ncbi.nlm.nih.gov/articles/PMC5334499/)"
    )


def test_enrichment_links_caption_pdf_only() -> None:
    caption = enrichment_links_caption(
        None,
        "https://pmc-oa-opendata.s3.amazonaws.com/oa_pdf/PMC5334499.2.pdf",
    )

    assert caption == (
        "[Open access PDF]"
        "(https://pmc-oa-opendata.s3.amazonaws.com/oa_pdf/PMC5334499.2.pdf)"
    )


def test_enrichment_links_caption_both() -> None:
    caption = enrichment_links_caption(
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC5334499/",
        "https://pmc-oa-opendata.s3.amazonaws.com/oa_pdf/PMC5334499.2.pdf",
    )

    assert caption == (
        "[PMC article](https://pmc.ncbi.nlm.nih.gov/articles/PMC5334499/) · "
        "[Open access PDF]"
        "(https://pmc-oa-opendata.s3.amazonaws.com/oa_pdf/PMC5334499.2.pdf)"
    )


def test_may_submit_regenerate_when_both_terminal() -> None:
    assert (
        may_submit_regenerate_paper(
            PaperAspectStatus.succeeded,
            PaperAspectStatus.unavailable,
        )
        is True
    )
    assert (
        may_submit_regenerate_paper(
            PaperAspectStatus.failed,
            PaperAspectStatus.not_started,
        )
        is False
    )
    assert (
        may_submit_regenerate_paper(
            PaperAspectStatus.succeeded,
            PaperAspectStatus.not_started,
        )
        is False
    )
    assert (
        may_submit_regenerate_paper(
            PaperAspectStatus.not_started,
            PaperAspectStatus.not_started,
        )
        is False
    )
    assert (
        may_submit_regenerate_paper(
            PaperAspectStatus.succeeded,
            PaperAspectStatus.succeeded,
        )
        is True
    )
    assert (
        may_submit_regenerate_paper(
            PaperAspectStatus.failed,
            PaperAspectStatus.failed,
        )
        is True
    )


def test_regenerate_button_label() -> None:
    assert REGENERATE_BUTTON_LABEL == "Regenerate"


def test_regenerate_deployment_ref_in_enqueue_hint() -> None:
    hint = prefect_enqueue_error_hint(None, REGENERATE_PAPER_DEPLOYMENT_REF)

    assert REGENERATE_PAPER_DEPLOYMENT_REF in hint
    assert REGENERATE_PAPER_DEPLOYMENT_REF == "regenerate_paper/default"


def test_prefect_enqueue_error_hint_unset_url() -> None:
    hint = prefect_enqueue_error_hint(None, REGENERATE_PAPER_DEPLOYMENT_REF)

    assert "PREFECT_API_URL=(unset)" in hint
    assert REGENERATE_PAPER_DEPLOYMENT_REF in hint
    assert "prefect-server" not in hint


def test_prefect_enqueue_error_hint_uses_configured_url() -> None:
    url = "http://custom-prefect:9999/api"
    hint = prefect_enqueue_error_hint(url, REGENERATE_PAPER_DEPLOYMENT_REF)

    assert f"PREFECT_API_URL={url}" in hint
    assert REGENERATE_PAPER_DEPLOYMENT_REF in hint
    assert "prefect-server" not in hint


def test_brief_progress_label_blocked_unavailable() -> None:
    assert (
        brief_progress_label(
            full_text_status=PaperAspectStatus.unavailable,
            brief_status=None,
            skipped_already_succeeded=False,
        )
        == "Blocked (no full text)"
    )


def test_brief_progress_label_blocked_failed() -> None:
    assert (
        brief_progress_label(
            full_text_status=PaperAspectStatus.failed,
            brief_status=None,
            skipped_already_succeeded=False,
        )
        == "Blocked (no full text)"
    )


def test_brief_progress_label_fulfilling_when_full_text_not_started() -> None:
    assert (
        brief_progress_label(
            full_text_status=PaperAspectStatus.not_started,
            brief_status=None,
            skipped_already_succeeded=False,
        )
        == "Fulfilling"
    )


def test_brief_progress_label_fulfilling_no_row() -> None:
    assert (
        brief_progress_label(
            full_text_status=PaperAspectStatus.succeeded,
            brief_status=None,
            skipped_already_succeeded=False,
        )
        == "Fulfilling"
    )


def test_brief_progress_label_fulfilling_not_started() -> None:
    assert (
        brief_progress_label(
            full_text_status=PaperAspectStatus.succeeded,
            brief_status=PaperAspectStatus.not_started,
            skipped_already_succeeded=False,
        )
        == "Fulfilling"
    )


def test_brief_progress_label_succeeded() -> None:
    assert (
        brief_progress_label(
            full_text_status=PaperAspectStatus.succeeded,
            brief_status=PaperAspectStatus.succeeded,
            skipped_already_succeeded=False,
        )
        == "Succeeded"
    )


def test_brief_progress_label_failed() -> None:
    assert (
        brief_progress_label(
            full_text_status=PaperAspectStatus.succeeded,
            brief_status=PaperAspectStatus.failed,
            skipped_already_succeeded=False,
        )
        == "Failed"
    )


def test_brief_progress_label_skipped_already_done() -> None:
    assert (
        brief_progress_label(
            full_text_status=PaperAspectStatus.succeeded,
            brief_status=PaperAspectStatus.succeeded,
            skipped_already_succeeded=True,
        )
        == "Skipped (already done)"
    )


def test_split_brief_error_message_separates_validation_and_assistant() -> None:
    raw = '{summary: "x"}'
    stored = (
        "1 validation error for PaperBriefContent\n"
        "Invalid JSON: Expecting property name enclosed in double quotes\n\n"
        "Assistant output:\n"
        f"{raw}"
    )

    caption, assistant = split_brief_error_message(stored)

    assert "validation error" in caption.lower()
    assert raw not in caption
    assert assistant == raw


def test_split_brief_error_message_without_assistant_dump() -> None:
    stored = "OPENAI_API_KEY is not set"

    caption, assistant = split_brief_error_message(stored)

    assert caption == stored
    assert assistant is None


def test_format_brief_progress_caption_omits_assistant_dump() -> None:
    raw = '{summary: "illegal"}'
    stored = (
        "Expecting property name enclosed in double quotes\n\n"
        "Assistant output:\n"
        f"{raw}"
    )

    caption = format_brief_progress_caption(
        label="Failed",
        error_message=stored,
    )

    assert caption.startswith("brief Failed")
    assert "Expecting property name enclosed in double quotes" in caption
    assert raw not in caption
    assert "Assistant output:" not in caption


def test_format_brief_progress_caption_without_error() -> None:
    caption = format_brief_progress_caption(
        label="Succeeded",
        error_message=None,
    )

    assert caption == "brief Succeeded"


def test_paper_ingest_row_is_terminal_when_full_text_blocked() -> None:
    assert (
        paper_ingest_row_is_terminal(
            PaperAspectStatus.succeeded,
            PaperAspectStatus.unavailable,
            None,
        )
        is True
    )


def test_paper_ingest_row_is_terminal_waits_for_brief() -> None:
    assert (
        paper_ingest_row_is_terminal(
            PaperAspectStatus.succeeded,
            PaperAspectStatus.succeeded,
            None,
        )
        is False
    )
    assert (
        paper_ingest_row_is_terminal(
            PaperAspectStatus.succeeded,
            PaperAspectStatus.succeeded,
            PaperAspectStatus.succeeded,
        )
        is True
    )
