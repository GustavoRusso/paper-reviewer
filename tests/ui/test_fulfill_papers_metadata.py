"""Fulfill papers metadata page helpers: prerequisites and status labels."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from paper_reviewer.schemas.topic_brief_generation.paper_archiving import (
    PaperArchivingResult,
)
from paper_reviewer.flows.serve import INFORM_DEPLOYMENT_REF
from paper_reviewer.ui.fulfill_papers_metadata import (
    enrichment_links_caption,
    fulfill_prerequisites_met,
    inform_status_label,
    prefect_enqueue_error_hint,
)
from paper_reviewer.ui.topic_intake import (
    ARCHIVING_RESULT_KEY,
    FULFILL_ENQUEUE_RESULT_KEY,
    PUBLIC_ID_KEY,
)


def test_prerequisites_met_when_archiving_result_and_public_id_present() -> None:
    state = {
        ARCHIVING_RESULT_KEY: PaperArchivingResult(papers=[], skipped=[], errors=[]),
        PUBLIC_ID_KEY: uuid4(),
    }

    assert fulfill_prerequisites_met(state) is True


def test_prerequisites_missing_without_archiving_result() -> None:
    state = {PUBLIC_ID_KEY: uuid4()}

    assert fulfill_prerequisites_met(state) is False


def test_prerequisites_missing_without_public_id() -> None:
    state = {
        ARCHIVING_RESULT_KEY: PaperArchivingResult(papers=[], skipped=[], errors=[]),
    }

    assert fulfill_prerequisites_met(state) is False


def test_inform_status_label_fulfilled() -> None:
    assert (
        inform_status_label(
            source_informed_at=datetime(2026, 8, 12, tzinfo=UTC),
            source_inform_error_message=None,
            skipped_already_informed=False,
        )
        == "Fulfilled"
    )


def test_inform_status_label_skipped_already_done() -> None:
    assert (
        inform_status_label(
            source_informed_at=datetime(2026, 8, 12, tzinfo=UTC),
            source_inform_error_message=None,
            skipped_already_informed=True,
        )
        == "Skipped (already done)"
    )


def test_inform_status_label_failed() -> None:
    assert (
        inform_status_label(
            source_informed_at=None,
            source_inform_error_message="HTTP 429",
            skipped_already_informed=False,
        )
        == "Failed"
    )


def test_inform_status_label_fulfilling() -> None:
    assert (
        inform_status_label(
            source_informed_at=None,
            source_inform_error_message=None,
            skipped_already_informed=False,
        )
        == "Fulfilling from source"
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
    hint = prefect_enqueue_error_hint(None, INFORM_DEPLOYMENT_REF)

    assert "PREFECT_API_URL=(unset)" in hint
    assert INFORM_DEPLOYMENT_REF in hint
    assert "prefect-server" not in hint


def test_prefect_enqueue_error_hint_uses_configured_url() -> None:
    url = "http://custom-prefect:9999/api"
    hint = prefect_enqueue_error_hint(url, INFORM_DEPLOYMENT_REF)

    assert f"PREFECT_API_URL={url}" in hint
    assert INFORM_DEPLOYMENT_REF in hint
    assert "prefect-server" not in hint
