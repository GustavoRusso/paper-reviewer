"""inform_source_record: default skip and source-record writes."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.paper import get_paper_by_id
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.topic_scope.fulfill_papers_metadata import (
    inform_source_record,
)
from tests.topic_scope.fulfill_papers_metadata.helpers import (
    create_test_paper,
    mapped_photo,
)


def test_skips_when_source_succeeded(session_factory: sessionmaker[Session]) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.unavailable,
    )
    calls: list[str] = []

    result = inform_source_record(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: calls.append("fetch") or mapped_photo(),
    )

    assert result.paper_id == paper_id
    assert result.status is PaperAspectStatus.succeeded
    assert result.error_message is None
    assert calls == []

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.title == "Old title"
        assert paper.full_text_status is PaperAspectStatus.unavailable
    finally:
        session.close()


def test_skips_when_source_failed(session_factory: sessionmaker[Session]) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.failed,
        source_record_error_message="prior failure",
    )
    calls: list[str] = []

    result = inform_source_record(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: calls.append("fetch") or mapped_photo(),
    )

    assert result.status is PaperAspectStatus.failed
    assert result.error_message == "prior failure"
    assert calls == []


def test_skips_when_source_unavailable(session_factory: sessionmaker[Session]) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_id="other",
        uid="9",
        source_record_status=PaperAspectStatus.unavailable,
    )
    calls: list[str] = []

    result = inform_source_record(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: calls.append("fetch") or mapped_photo(),
    )

    assert result.status is PaperAspectStatus.unavailable
    assert result.error_message is None
    assert calls == []


def test_writes_source_record_and_promotes(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(session_factory)

    result = inform_source_record(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: mapped_photo(),
    )

    assert result.status is PaperAspectStatus.succeeded
    assert result.error_message is None

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.source_record_status is PaperAspectStatus.succeeded
        assert paper.source_record_error_message is None
        assert paper.full_text_status is PaperAspectStatus.not_started
        assert paper.full_text_error_message is None
        assert paper.source_record is not None
        assert paper.title == "New title"
        assert paper.authors == ["Ada Lovelace"]
        assert paper.journal == "Orphanet J Rare Dis"
        assert paper.published_year == 2024
        assert paper.pub_date == date(2024, 3, 15)
        assert paper.abstract_text == "Background text. Methods text."
        assert paper.pmcid is None
        assert paper.pmc_article_url is None
        assert paper.doi == "10.1000/EXAMPLE"
        assert paper.source_uid == "100"
    finally:
        session.close()


def test_empty_abstract_still_succeeds(session_factory: sessionmaker[Session]) -> None:
    paper_id = create_test_paper(session_factory)
    payload = mapped_photo()
    payload["abstract_text"] = None
    payload["source_record"]["abstract"]["parts"] = []

    result = inform_source_record(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: payload,
    )

    assert result.status is PaperAspectStatus.succeeded

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.abstract_text is None
        assert paper.source_record is not None
        assert paper.full_text_status is PaperAspectStatus.not_started
    finally:
        session.close()


def test_sets_pmcid_and_derives_pmc_article_url(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(session_factory)
    payload = mapped_photo()
    payload["pmcid"] = "PMC5334499"

    result = inform_source_record(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: payload,
    )

    assert result.status is PaperAspectStatus.succeeded

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.pmcid == "PMC5334499"
        assert (
            paper.pmc_article_url
            == "https://pmc.ncbi.nlm.nih.gov/articles/PMC5334499/"
        )
        assert paper.full_text_status is PaperAspectStatus.not_started
        assert paper.full_text_plain is None
    finally:
        session.close()


def test_unsupported_source_marks_unavailable(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(session_factory, source_id="other", uid="9")

    result = inform_source_record(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: mapped_photo(),
    )

    assert result.status is PaperAspectStatus.unavailable
    assert result.error_message is None

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.source_record_status is PaperAspectStatus.unavailable
        assert paper.source_record_error_message is None
        assert paper.full_text_status is PaperAspectStatus.not_started
    finally:
        session.close()


def test_fetch_error_marks_source_failed(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper_id = create_test_paper(session_factory)
    calls: list[str] = []
    sleep_calls: list[float] = []

    def fetch(_source_id: str, _source_uid: str) -> dict[str, Any]:
        calls.append("fetch")
        raise RuntimeError("HTTP 500 from NCBI EFetch: server error")

    monkeypatch.setattr(
        "paper_reviewer.topic_scope.fulfill_papers_metadata.inform.time.sleep",
        sleep_calls.append,
    )

    result = inform_source_record(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=fetch,
    )

    assert result.status is PaperAspectStatus.failed
    assert "500" in (result.error_message or "")
    assert calls == ["fetch", "fetch", "fetch"]
    assert sleep_calls == [0.5, 0.5]

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.source_record_status is PaperAspectStatus.failed
        assert "500" in (paper.source_record_error_message or "")
        assert paper.full_text_status is PaperAspectStatus.not_started
    finally:
        session.close()


def test_rate_limit_retries_do_not_count_toward_failure_budget(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper_id = create_test_paper(session_factory)
    calls: list[str] = []
    sleep_calls: list[float] = []
    rate_limit_delays = [0.7, 1.2, 1.8, 0.9]

    def fetch(_source_id: str, _source_uid: str) -> dict[str, Any]:
        calls.append("fetch")
        if len(calls) <= 4:
            raise RuntimeError(
                'HTTP 429 from NCBI EFetch: {"error":"API rate limit exceeded"}'
            )
        return mapped_photo()

    monkeypatch.setattr(
        "paper_reviewer.topic_scope.fulfill_papers_metadata.inform.time.sleep",
        sleep_calls.append,
    )
    monkeypatch.setattr(
        "paper_reviewer.topic_scope.fulfill_papers_metadata.inform."
        "_rate_limit_retry_delay_seconds",
        lambda: rate_limit_delays[len(sleep_calls)],
    )

    result = inform_source_record(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=fetch,
    )

    assert result.status is PaperAspectStatus.succeeded
    assert result.error_message is None
    assert calls == ["fetch", "fetch", "fetch", "fetch", "fetch"]
    assert sleep_calls == rate_limit_delays
    assert all(0.5 < delay < 2.0 for delay in sleep_calls)

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.source_record_status is PaperAspectStatus.succeeded
        assert paper.title == "New title"
        assert paper.full_text_status is PaperAspectStatus.not_started
    finally:
        session.close()


def test_rate_limit_then_hard_errors_still_respect_failure_budget(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper_id = create_test_paper(session_factory)
    calls: list[str] = []
    sleep_calls: list[float] = []
    rate_limit_delays = [0.8, 1.1]

    def fetch(_source_id: str, _source_uid: str) -> dict[str, Any]:
        calls.append("fetch")
        if len(calls) <= 2:
            raise RuntimeError(
                'HTTP 429 from NCBI EFetch: {"error":"API rate limit exceeded"}'
            )
        raise RuntimeError("HTTP 500 from NCBI EFetch: server error")

    monkeypatch.setattr(
        "paper_reviewer.topic_scope.fulfill_papers_metadata.inform.time.sleep",
        sleep_calls.append,
    )
    monkeypatch.setattr(
        "paper_reviewer.topic_scope.fulfill_papers_metadata.inform."
        "_rate_limit_retry_delay_seconds",
        lambda: rate_limit_delays[len([s for s in sleep_calls if s != 0.5])],
    )

    result = inform_source_record(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=fetch,
    )

    assert result.status is PaperAspectStatus.failed
    assert "500" in (result.error_message or "")
    # 2 rate-limit soft retries + 3 hard-failure attempts
    assert calls == ["fetch", "fetch", "fetch", "fetch", "fetch"]
    assert sleep_calls == [0.8, 1.1, 0.5, 0.5]

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.source_record_status is PaperAspectStatus.failed
        assert "500" in (paper.source_record_error_message or "")
        assert paper.full_text_status is PaperAspectStatus.not_started
    finally:
        session.close()


def test_fetch_succeeds_after_transient_failures(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper_id = create_test_paper(session_factory)
    calls: list[str] = []
    sleep_calls: list[float] = []

    def fetch(_source_id: str, _source_uid: str) -> dict[str, Any]:
        calls.append("fetch")
        if len(calls) < 3:
            raise RuntimeError("transient EFetch error")
        return mapped_photo()

    monkeypatch.setattr(
        "paper_reviewer.topic_scope.fulfill_papers_metadata.inform.time.sleep",
        sleep_calls.append,
    )

    result = inform_source_record(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=fetch,
    )

    assert result.status is PaperAspectStatus.succeeded
    assert result.error_message is None
    assert calls == ["fetch", "fetch", "fetch"]
    assert sleep_calls == [0.5, 0.5]

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.title == "New title"
        assert paper.full_text_status is PaperAspectStatus.not_started
    finally:
        session.close()


def test_missing_paper_marks_failed(session_factory: sessionmaker[Session]) -> None:
    result = inform_source_record(
        999_999,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: mapped_photo(),
    )

    assert result.paper_id == 999_999
    assert result.status is PaperAspectStatus.failed
    assert result.error_message is not None


def test_force_true_refetches_succeeded_source(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.unavailable,
    )
    calls: list[str] = []

    result = inform_source_record(
        paper_id,
        force=True,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: calls.append("fetch") or mapped_photo(),
    )

    assert result.status is PaperAspectStatus.succeeded
    assert calls == ["fetch"]

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.title == "New title"
        assert paper.source_record_error_message is None
        assert paper.full_text_status is PaperAspectStatus.unavailable
    finally:
        session.close()


def test_force_true_unsupported_source_still_unavailable(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_id="other",
        uid="9",
        source_record_status=PaperAspectStatus.unavailable,
    )
    calls: list[str] = []

    result = inform_source_record(
        paper_id,
        force=True,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: calls.append("fetch") or mapped_photo(),
    )

    assert result.status is PaperAspectStatus.unavailable
    assert calls == []
