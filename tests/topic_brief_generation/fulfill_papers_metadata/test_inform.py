"""inform_paper_from_source: idempotent source-inform for one Paper."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.base import Base
from paper_reviewer.models.topic_brief_generation import create_paper, get_paper_by_id
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    InformOutcome,
)
from paper_reviewer.topic_brief_generation.fulfill_papers_metadata.inform import (
    inform_paper_from_source,
)


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    import paper_reviewer.models.topic_brief_generation.paper  # noqa: F401

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    try:
        yield factory
    finally:
        engine.dispose()


def _create(
    factory: sessionmaker[Session],
    *,
    source_id: str = "pubmed",
    uid: str = "100",
    informed: bool = False,
    failed: bool = False,
) -> int:
    session = factory()
    try:
        paper = create_paper(
            session,
            doi="10.1000/EXAMPLE",
            source_id=source_id,
            source_uid=uid,
            title="Old title",
            authors=["Old Author"],
            url="https://pubmed.ncbi.nlm.nih.gov/100/",
            journal="Old Journal",
            published_year=2020,
        )
        if informed:
            paper.source_informed_at = datetime(2026, 1, 1, tzinfo=UTC)
            paper.source_record = {"abstract": {"parts": []}}
        if failed:
            paper.source_inform_error_message = "prior failure"
        session.commit()
        return paper.id
    finally:
        session.close()


def _mapped_photo() -> dict[str, Any]:
    return {
        "source_record": {
            "abstract": {
                "parts": [
                    {"label": "BACKGROUND", "text": "Background text."},
                    {"label": "METHODS", "text": "Methods text."},
                ],
                "copyright": None,
                "other_abstracts": [],
            },
            "dates": {
                "pub_date": {"year": 2024, "month": 3, "day": 15},
                "article_date_electronic": None,
                "date_completed": None,
                "date_revised": None,
                "history": [],
            },
            "journal_detail": {"medline_ta": "Orphanet J Rare Dis"},
            "types_language": {},
            "indexing": {},
            "funding": {},
            "coi_notes": {},
        },
        "title": "New title",
        "authors": ["Ada Lovelace"],
        "journal": "Orphanet J Rare Dis",
        "published_year": 2024,
        "pub_date": date(2024, 3, 15),
        "abstract_text": "Background text. Methods text.",
        "pmcid": None,
    }


def test_already_informed_is_noop(session_factory: sessionmaker[Session]) -> None:
    paper_id = _create(session_factory, informed=True)
    calls: list[str] = []

    def fetch(_source_id: str, _source_uid: str) -> dict[str, Any]:
        calls.append("fetch")
        return _mapped_photo()

    result = inform_paper_from_source(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=fetch,
    )

    assert result.outcome == InformOutcome.skipped_already_informed
    assert result.paper_id == paper_id
    assert result.error_message is None
    assert calls == []

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.title == "Old title"
    finally:
        session.close()


def test_fulfill_writes_source_record_and_promotes(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = _create(session_factory, failed=True)

    result = inform_paper_from_source(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: _mapped_photo(),
    )

    assert result.outcome == InformOutcome.fulfilled
    assert result.error_message is None

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.source_informed_at is not None
        assert paper.source_inform_error_message is None
        assert paper.source_record is not None
        assert paper.title == "New title"
        assert paper.authors == ["Ada Lovelace"]
        assert paper.journal == "Orphanet J Rare Dis"
        assert paper.published_year == 2024
        assert paper.pub_date == date(2024, 3, 15)
        assert paper.abstract_text == "Background text. Methods text."
        assert paper.pmcid is None
        assert paper.pmc_article_url is None
        assert paper.pmcid_version is None
        assert paper.is_open_access is None
        assert paper.full_text_plain is None
        assert paper.open_access_pdf_url is None
        assert paper.doi == "10.1000/EXAMPLE"
        assert paper.source_uid == "100"
    finally:
        session.close()


def test_fulfill_sets_pmcid_and_derives_pmc_article_url(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = _create(session_factory)
    payload = _mapped_photo()
    payload["pmcid"] = "PMC5334499"

    result = inform_paper_from_source(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: payload,
    )

    assert result.outcome == InformOutcome.fulfilled

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.pmcid == "PMC5334499"
        assert (
            paper.pmc_article_url
            == "https://pmc.ncbi.nlm.nih.gov/articles/PMC5334499/"
        )
        assert paper.source_informed_at is not None
    finally:
        session.close()


def test_fulfill_applies_cloud_enrichment_fields(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = _create(session_factory)
    payload = _mapped_photo()
    payload.update(
        {
            "pmcid": "PMC5334499",
            "pmcid_version": 2,
            "is_open_access": True,
            "full_text_plain": "Full article text from Cloud.",
            "open_access_pdf_url": (
                "https://pmc-oa-opendata.s3.amazonaws.com/oa_pdf/PMC5334499.2.pdf"
            ),
            "pmc_article_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5334499/",
        }
    )

    result = inform_paper_from_source(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: payload,
    )

    assert result.outcome == InformOutcome.fulfilled

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.pmcid == "PMC5334499"
        assert paper.pmcid_version == 2
        assert paper.is_open_access is True
        assert paper.full_text_plain == "Full article text from Cloud."
        assert paper.open_access_pdf_url == (
            "https://pmc-oa-opendata.s3.amazonaws.com/oa_pdf/PMC5334499.2.pdf"
        )
        assert (
            paper.pmc_article_url
            == "https://pmc.ncbi.nlm.nih.gov/articles/PMC5334499/"
        )
    finally:
        session.close()


def test_already_informed_does_not_overwrite_enrichment(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = _create(session_factory, informed=True)
    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        paper.pmcid = "PMC111"
        paper.full_text_plain = "Kept text"
        session.commit()
    finally:
        session.close()

    payload = _mapped_photo()
    payload.update(
        {
            "pmcid": "PMC999",
            "full_text_plain": "Should not apply",
        }
    )

    result = inform_paper_from_source(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: payload,
    )

    assert result.outcome == InformOutcome.skipped_already_informed

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.pmcid == "PMC111"
        assert paper.full_text_plain == "Kept text"
        assert paper.title == "Old title"
    finally:
        session.close()


def test_unsupported_source_marks_failed(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = _create(session_factory, source_id="other", uid="9")

    result = inform_paper_from_source(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: _mapped_photo(),
    )

    assert result.outcome == InformOutcome.failed
    assert result.error_message is not None

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.source_informed_at is None
        assert paper.source_inform_error_message is not None
    finally:
        session.close()


def test_fetch_error_marks_failed(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper_id = _create(session_factory)
    calls: list[str] = []
    sleep_calls: list[float] = []

    def fetch(_source_id: str, _source_uid: str) -> dict[str, Any]:
        calls.append("fetch")
        raise RuntimeError("HTTP 429 from NCBI EFetch")

    monkeypatch.setattr(
        "paper_reviewer.topic_brief_generation.fulfill_papers_metadata.inform.time.sleep",
        sleep_calls.append,
    )

    result = inform_paper_from_source(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=fetch,
    )

    assert result.outcome == InformOutcome.failed
    assert "429" in (result.error_message or "")
    assert calls == ["fetch", "fetch", "fetch"]
    assert sleep_calls == [0.5, 0.5]

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.source_informed_at is None
        assert "429" in (paper.source_inform_error_message or "")
    finally:
        session.close()


def test_fetch_succeeds_after_transient_failures(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper_id = _create(session_factory)
    calls: list[str] = []
    sleep_calls: list[float] = []

    def fetch(_source_id: str, _source_uid: str) -> dict[str, Any]:
        calls.append("fetch")
        if len(calls) < 3:
            raise RuntimeError("transient EFetch error")
        return _mapped_photo()

    monkeypatch.setattr(
        "paper_reviewer.topic_brief_generation.fulfill_papers_metadata.inform.time.sleep",
        sleep_calls.append,
    )

    result = inform_paper_from_source(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=fetch,
    )

    assert result.outcome == InformOutcome.fulfilled
    assert result.error_message is None
    assert calls == ["fetch", "fetch", "fetch"]
    assert sleep_calls == [0.5, 0.5]

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.source_informed_at is not None
        assert paper.source_inform_error_message is None
        assert paper.title == "New title"
    finally:
        session.close()


def test_fetch_exhausts_retries_then_marks_failed(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper_id = _create(session_factory)
    calls: list[str] = []
    sleep_calls: list[float] = []

    def fetch(_source_id: str, _source_uid: str) -> dict[str, Any]:
        calls.append("fetch")
        raise RuntimeError("HTTP 429 from NCBI EFetch")

    monkeypatch.setattr(
        "paper_reviewer.topic_brief_generation.fulfill_papers_metadata.inform.time.sleep",
        sleep_calls.append,
    )

    result = inform_paper_from_source(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=fetch,
    )

    assert result.outcome == InformOutcome.failed
    assert "429" in (result.error_message or "")
    assert calls == ["fetch", "fetch", "fetch"]
    assert sleep_calls == [0.5, 0.5]

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.source_informed_at is None
        assert "429" in (paper.source_inform_error_message or "")
    finally:
        session.close()


def test_missing_paper_marks_failed(session_factory: sessionmaker[Session]) -> None:
    result = inform_paper_from_source(
        999_999,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: _mapped_photo(),
    )

    assert result.outcome == InformOutcome.failed
    assert result.paper_id == 999_999
