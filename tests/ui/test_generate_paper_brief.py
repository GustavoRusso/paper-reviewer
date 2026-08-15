"""Generate paper brief page helpers: prerequisites and status labels."""

from __future__ import annotations

from uuid import uuid4

from paper_reviewer.flows.serve import CREATE_PAPER_BRIEF_DEPLOYMENT_REF
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_brief_generation.paper_archiving import (
    PaperArchivingResult,
)
from paper_reviewer.ui.fulfill_papers_metadata import prefect_enqueue_error_hint
from paper_reviewer.ui.generate_paper_brief import (
    brief_prerequisites_met,
    brief_progress_label,
)
from paper_reviewer.ui.new_topic_brief import (
    ARCHIVING_RESULT_KEY,
    GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY,
)


def test_prerequisites_met_when_archiving_result_and_public_id_present() -> None:
    state = {
        ARCHIVING_RESULT_KEY: PaperArchivingResult(papers=[], skipped=[], errors=[]),
    }

    assert brief_prerequisites_met(state, public_id=uuid4()) is True


def test_prerequisites_missing_without_archiving_result() -> None:
    assert brief_prerequisites_met({}, public_id=uuid4()) is False


def test_prerequisites_missing_without_public_id() -> None:
    state = {
        ARCHIVING_RESULT_KEY: PaperArchivingResult(papers=[], skipped=[], errors=[]),
    }

    assert brief_prerequisites_met(state, public_id=None) is False


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
