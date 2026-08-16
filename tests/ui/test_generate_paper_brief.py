"""Generate paper brief page helpers: prerequisites and status labels."""

from __future__ import annotations

from uuid import uuid4

from paper_reviewer.flows.serve import CREATE_PAPER_BRIEF_DEPLOYMENT_REF
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.paper_archiving import (
    PaperArchivingResult,
)
from paper_reviewer.ui.fulfill_papers_metadata import prefect_enqueue_error_hint
from paper_reviewer.ui.generate_paper_brief import (
    brief_prerequisites_met,
    brief_progress_label,
    format_brief_progress_caption,
    split_brief_error_message,
)
from paper_reviewer.ui.topic_intake import (
    ARCHIVING_RESULT_KEY,
    GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY,
)


def test_prerequisites_met_when_archiving_result_and_topic_scope_key_present() -> None:
    state = {
        ARCHIVING_RESULT_KEY: PaperArchivingResult(papers=[], skipped=[], errors=[]),
    }

    assert brief_prerequisites_met(state, topic_scope_key=uuid4()) is True


def test_prerequisites_missing_without_archiving_result() -> None:
    assert brief_prerequisites_met({}, topic_scope_key=uuid4()) is False


def test_prerequisites_missing_without_topic_scope_key() -> None:
    state = {
        ARCHIVING_RESULT_KEY: PaperArchivingResult(papers=[], skipped=[], errors=[]),
    }

    assert brief_prerequisites_met(state, topic_scope_key=None) is False


def test_brief_progress_label_incomplete() -> None:
    assert (
        brief_progress_label(
            full_text_status=PaperAspectStatus.not_started,
            brief_status=None,
            skipped_already_succeeded=False,
        )
        == "Incomplete (fulfill papers metadata first)"
    )


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


def test_brief_progress_label_skipped_already_done() -> None:
    assert (
        brief_progress_label(
            full_text_status=PaperAspectStatus.succeeded,
            brief_status=PaperAspectStatus.succeeded,
            skipped_already_succeeded=True,
        )
        == "Skipped (already done)"
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


def test_generate_paper_brief_enqueue_result_key_constant() -> None:
    assert (
        GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY == "generate_paper_brief_enqueue_result"
    )


def test_brief_deployment_ref_in_enqueue_hint() -> None:
    hint = prefect_enqueue_error_hint(None, CREATE_PAPER_BRIEF_DEPLOYMENT_REF)

    assert CREATE_PAPER_BRIEF_DEPLOYMENT_REF in hint
    assert CREATE_PAPER_BRIEF_DEPLOYMENT_REF == "create_paper_brief/default"


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
    assert "Invalid JSON" in caption
    assert raw not in caption
    assert "Assistant output:" not in caption
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
        doi="10.1/ABC",
        label="Failed",
        error_message=stored,
    )

    assert "DOI `10.1/ABC`" in caption
    assert "brief Failed" in caption
    assert "Expecting property name enclosed in double quotes" in caption
    assert raw not in caption
    assert "Assistant output:" not in caption


def test_format_brief_progress_caption_without_error() -> None:
    caption = format_brief_progress_caption(
        doi="10.1/ABC",
        label="Succeeded",
        error_message=None,
    )

    assert caption == "DOI `10.1/ABC` · brief Succeeded"
