"""Fulfill papers metadata page helpers: prerequisites and status labels."""

from __future__ import annotations

from uuid import uuid4

from paper_reviewer.flows.serve import FULFILL_DEPLOYMENT_REF, REGENERATE_PAPER_DEPLOYMENT_REF
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_brief_generation.paper_archiving import (
    PaperArchivingResult,
)
from paper_reviewer.ui.fulfill_papers_metadata import (
    REGENERATE_BUTTON_LABEL,
    aspect_status_label,
    enrichment_links_caption,
    fulfill_prerequisites_met,
    may_submit_regenerate_paper,
    prefect_enqueue_error_hint,
)
from paper_reviewer.ui.new_topic_brief import (
    ARCHIVING_RESULT_KEY,
    FULFILL_ENQUEUE_RESULT_KEY,
)


def test_prerequisites_met_when_archiving_result_and_public_id_present() -> None:
    state = {
        ARCHIVING_RESULT_KEY: PaperArchivingResult(papers=[], skipped=[], errors=[]),
    }

    assert fulfill_prerequisites_met(state, public_id=uuid4()) is True


def test_prerequisites_missing_without_archiving_result() -> None:
    assert fulfill_prerequisites_met({}, public_id=uuid4()) is False


def test_prerequisites_missing_without_public_id() -> None:
    state = {
        ARCHIVING_RESULT_KEY: PaperArchivingResult(papers=[], skipped=[], errors=[]),
    }

    assert fulfill_prerequisites_met(state, public_id=None) is False


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


def test_fulfill_enqueue_result_key_constant() -> None:
    assert FULFILL_ENQUEUE_RESULT_KEY == "fulfill_papers_metadata_enqueue_result"


def test_prefect_enqueue_error_hint_unset_url() -> None:
    hint = prefect_enqueue_error_hint(None, FULFILL_DEPLOYMENT_REF)

    assert "PREFECT_API_URL=(unset)" in hint
    assert FULFILL_DEPLOYMENT_REF in hint
    assert FULFILL_DEPLOYMENT_REF == "fulfill_paper_metadata/default"
    assert "prefect-server" not in hint


def test_prefect_enqueue_error_hint_uses_configured_url() -> None:
    url = "http://custom-prefect:9999/api"
    hint = prefect_enqueue_error_hint(url, FULFILL_DEPLOYMENT_REF)

    assert f"PREFECT_API_URL={url}" in hint
    assert FULFILL_DEPLOYMENT_REF in hint
    assert "prefect-server" not in hint


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
