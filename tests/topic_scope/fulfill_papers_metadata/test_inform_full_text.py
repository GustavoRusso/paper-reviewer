"""inform_full_text: default skip and PMC Cloud enrichment."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.paper import get_paper_by_id
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.topic_scope.fulfill_papers_metadata import (
    inform_full_text,
)
from tests.topic_scope.fulfill_papers_metadata.helpers import (
    cloud_hit,
    create_test_paper,
)


def test_skips_when_full_text_succeeded(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.succeeded,
        pmcid="PMC111",
    )
    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        paper.full_text_plain = "Kept text"
        session.commit()
    finally:
        session.close()
    cloud_calls: list[str | None] = []

    result = inform_full_text(
        paper_id,
        session_factory=session_factory,
        enrich_from_pmc_cloud=lambda pmcid: cloud_calls.append(pmcid) or cloud_hit(),
    )

    assert result.status is PaperAspectStatus.succeeded
    assert result.error_message is None
    assert cloud_calls == []

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.full_text_plain == "Kept text"
    finally:
        session.close()


def test_skips_when_full_text_failed(session_factory: sessionmaker[Session]) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.failed,
        pmcid="PMC5334499",
    )
    cloud_calls: list[str | None] = []

    result = inform_full_text(
        paper_id,
        session_factory=session_factory,
        enrich_from_pmc_cloud=lambda pmcid: cloud_calls.append(pmcid) or cloud_hit(),
    )

    assert result.status is PaperAspectStatus.failed
    assert cloud_calls == []


def test_skips_when_full_text_unavailable(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.unavailable,
        pmcid="PMC5334499",
    )
    cloud_calls: list[str | None] = []

    result = inform_full_text(
        paper_id,
        session_factory=session_factory,
        enrich_from_pmc_cloud=lambda pmcid: cloud_calls.append(pmcid) or cloud_hit(),
    )

    assert result.status is PaperAspectStatus.unavailable
    assert cloud_calls == []


def test_does_not_call_cloud_when_source_not_succeeded(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.failed,
        full_text_status=PaperAspectStatus.not_started,
        pmcid="PMC5334499",
    )
    cloud_calls: list[str | None] = []

    result = inform_full_text(
        paper_id,
        session_factory=session_factory,
        enrich_from_pmc_cloud=lambda pmcid: cloud_calls.append(pmcid) or cloud_hit(),
    )

    assert result.status is PaperAspectStatus.not_started
    assert result.error_message is None
    assert cloud_calls == []


def test_no_pmcid_marks_unavailable(session_factory: sessionmaker[Session]) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.not_started,
    )
    cloud_calls: list[str | None] = []

    result = inform_full_text(
        paper_id,
        session_factory=session_factory,
        enrich_from_pmc_cloud=lambda pmcid: cloud_calls.append(pmcid) or cloud_hit(),
    )

    assert result.status is PaperAspectStatus.unavailable
    assert result.error_message is None
    assert cloud_calls == []

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.full_text_status is PaperAspectStatus.unavailable
        assert paper.full_text_plain is None
    finally:
        session.close()


def test_cloud_hit_sets_succeeded(session_factory: sessionmaker[Session]) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.not_started,
        pmcid="PMC5334499",
    )
    cloud_calls: list[str | None] = []

    result = inform_full_text(
        paper_id,
        session_factory=session_factory,
        enrich_from_pmc_cloud=lambda pmcid: cloud_calls.append(pmcid) or cloud_hit(),
    )

    assert result.status is PaperAspectStatus.succeeded
    assert result.error_message is None
    assert cloud_calls == ["PMC5334499"]

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.pmcid_version == 2
        assert paper.is_open_access is True
        assert paper.full_text_plain == "Full article text from Cloud."
        assert paper.open_access_pdf_url == (
            "https://pmc-oa-opendata.s3.amazonaws.com/PMC5334499.2/PMC5334499.2.pdf"
        )
        assert (
            paper.pmc_article_url
            == "https://pmc.ncbi.nlm.nih.gov/articles/PMC5334499/"
        )
        assert paper.full_text_error_message is None
    finally:
        session.close()


def test_author_manuscript_succeeds_when_not_open_access(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.not_started,
        pmcid="PMC5334499",
    )

    result = inform_full_text(
        paper_id,
        session_factory=session_factory,
        enrich_from_pmc_cloud=lambda _pmcid: cloud_hit(
            is_open_access=False, pdf=False
        ),
    )

    assert result.status is PaperAspectStatus.succeeded

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.full_text_plain == "Full article text from Cloud."
        assert paper.is_open_access is False
        assert paper.open_access_pdf_url is None
    finally:
        session.close()


_LICENSE_STUB_BODY = (
    "Abstract\n\n"
    "Orthoflaviviruses depend on host metabolic resources.\n\n"
    "Full Text Availability\n\n"
    "The license terms selected by the author(s) for this preprint version "
    "do not permit archiving in PMC. The full text is available from the "
    "preprint server.\n"
)


@pytest.mark.parametrize("full_text_plain", ["", "   ", "\n\t"])
def test_blank_full_text_marks_unavailable_and_clears_body(
    session_factory: sessionmaker[Session],
    full_text_plain: str,
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.not_started,
        pmcid="PMC5334499",
    )

    result = inform_full_text(
        paper_id,
        session_factory=session_factory,
        enrich_from_pmc_cloud=lambda _pmcid: {
            **cloud_hit(),
            "full_text_plain": full_text_plain,
        },
    )

    assert result.status is PaperAspectStatus.unavailable
    assert result.error_message is None

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.full_text_status is PaperAspectStatus.unavailable
        assert paper.full_text_plain is None
        assert paper.full_text_error_message is None
    finally:
        session.close()


def test_license_stub_marks_unavailable_and_stores_stripped_body(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.not_started,
        pmcid="PMC5334499",
    )
    hit = cloud_hit()
    hit["full_text_plain"] = f"\n{_LICENSE_STUB_BODY}  \n"

    result = inform_full_text(
        paper_id,
        session_factory=session_factory,
        enrich_from_pmc_cloud=lambda _pmcid: hit,
    )

    assert result.status is PaperAspectStatus.unavailable
    assert result.error_message is None

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.full_text_status is PaperAspectStatus.unavailable
        assert paper.full_text_plain == _LICENSE_STUB_BODY.strip()
        assert paper.pmcid_version == hit["pmcid_version"]
        assert paper.is_open_access is hit["is_open_access"]
        assert paper.pmc_article_url == hit["pmc_article_url"]
        assert paper.open_access_pdf_url == hit["open_access_pdf_url"]
        assert paper.full_text_error_message is None
    finally:
        session.close()


def test_cloud_version_without_usable_text_marks_unavailable(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.not_started,
        pmcid="PMC5334499",
    )

    result = inform_full_text(
        paper_id,
        session_factory=session_factory,
        enrich_from_pmc_cloud=lambda _pmcid: {
            "pmcid": "PMC5334499",
            "pmcid_version": 2,
            "is_open_access": True,
            "pmc_article_url": (
                "https://pmc.ncbi.nlm.nih.gov/articles/PMC5334499/"
            ),
        },
    )

    assert result.status is PaperAspectStatus.unavailable
    assert result.error_message is None

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.full_text_status is PaperAspectStatus.unavailable
        assert paper.full_text_plain is None
        assert paper.full_text_error_message is None
    finally:
        session.close()


def test_stores_stripped_body(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.not_started,
        pmcid="PMC5334499",
    )

    result = inform_full_text(
        paper_id,
        session_factory=session_factory,
        enrich_from_pmc_cloud=lambda _pmcid: {
            **cloud_hit(),
            "full_text_plain": "\nFull article text from Cloud.  \n",
        },
    )

    assert result.status is PaperAspectStatus.succeeded

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.full_text_plain == "Full article text from Cloud."
    finally:
        session.close()


def test_cloud_miss_marks_unavailable(session_factory: sessionmaker[Session]) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.not_started,
        pmcid="PMC5334499",
    )

    result = inform_full_text(
        paper_id,
        session_factory=session_factory,
        enrich_from_pmc_cloud=lambda _pmcid: {},
    )

    assert result.status is PaperAspectStatus.unavailable
    assert result.error_message is None

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.full_text_status is PaperAspectStatus.unavailable
        assert paper.full_text_plain is None
        assert paper.full_text_error_message is None
    finally:
        session.close()


def test_cloud_error_after_retries_marks_failed(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.not_started,
        pmcid="PMC5334499",
    )
    cloud_calls: list[str] = []
    sleep_calls: list[float] = []

    def enrich(_pmcid: str | None) -> dict[str, Any]:
        cloud_calls.append("cloud")
        raise RuntimeError("Cloud HTTP 500")

    monkeypatch.setattr(
        "paper_reviewer.topic_scope.fulfill_papers_metadata.inform.time.sleep",
        sleep_calls.append,
    )

    result = inform_full_text(
        paper_id,
        session_factory=session_factory,
        enrich_from_pmc_cloud=enrich,
    )

    assert result.status is PaperAspectStatus.failed
    assert "500" in (result.error_message or "")
    assert cloud_calls == ["cloud", "cloud", "cloud"]
    assert sleep_calls == [0.5, 0.5]

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.full_text_status is PaperAspectStatus.failed
        assert "500" in (paper.full_text_error_message or "")
        assert paper.full_text_plain is None
    finally:
        session.close()


def test_missing_paper_marks_failed(session_factory: sessionmaker[Session]) -> None:
    result = inform_full_text(
        999_999,
        session_factory=session_factory,
        enrich_from_pmc_cloud=lambda _pmcid: cloud_hit(),
    )

    assert result.paper_id == 999_999
    assert result.status is PaperAspectStatus.failed
    assert result.error_message is not None


def test_force_true_retries_unavailable_full_text(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.unavailable,
        pmcid="PMC5334499",
    )
    cloud_calls: list[str | None] = []

    result = inform_full_text(
        paper_id,
        force=True,
        session_factory=session_factory,
        enrich_from_pmc_cloud=lambda pmcid: cloud_calls.append(pmcid) or cloud_hit(),
    )

    assert result.status is PaperAspectStatus.succeeded
    assert cloud_calls == ["PMC5334499"]

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.full_text_plain == "Full article text from Cloud."
        assert paper.full_text_error_message is None
    finally:
        session.close()


def test_force_true_keeps_stored_license_stub_body(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.succeeded,
        pmcid="PMC5334499",
    )
    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        paper.full_text_plain = "Old article body."
        session.commit()
    finally:
        session.close()

    result = inform_full_text(
        paper_id,
        force=True,
        session_factory=session_factory,
        enrich_from_pmc_cloud=lambda _pmcid: {
            **cloud_hit(),
            "full_text_plain": _LICENSE_STUB_BODY,
        },
    )

    assert result.status is PaperAspectStatus.unavailable
    assert result.error_message is None

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.full_text_status is PaperAspectStatus.unavailable
        assert paper.full_text_plain == _LICENSE_STUB_BODY.strip()
        assert paper.full_text_error_message is None
    finally:
        session.close()


def test_force_true_does_not_call_cloud_when_source_not_succeeded(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.failed,
        full_text_status=PaperAspectStatus.unavailable,
        pmcid="PMC5334499",
    )
    cloud_calls: list[str | None] = []

    result = inform_full_text(
        paper_id,
        force=True,
        session_factory=session_factory,
        enrich_from_pmc_cloud=lambda pmcid: cloud_calls.append(pmcid) or cloud_hit(),
    )

    assert result.status is PaperAspectStatus.unavailable
    assert cloud_calls == []
