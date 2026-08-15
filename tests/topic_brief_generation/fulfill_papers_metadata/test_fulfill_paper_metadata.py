"""fulfill_paper_metadata: source then full text with default skip."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.paper import get_paper_by_id
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.topic_brief_generation.fulfill_papers_metadata import (
    fulfill_paper_metadata,
)
from tests.topic_brief_generation.fulfill_papers_metadata.helpers import (
    cloud_hit,
    create_test_paper,
    mapped_photo,
)


def test_backfill_skips_source_and_runs_cloud(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.not_started,
        pmcid="PMC5334499",
    )
    fetch_calls: list[str] = []
    cloud_calls: list[str | None] = []

    result = fulfill_paper_metadata(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: fetch_calls.append("fetch")
        or mapped_photo(),
        enrich_from_pmc_cloud=lambda pmcid: cloud_calls.append(pmcid) or cloud_hit(),
    )

    assert result.paper_id == paper_id
    assert result.source_record.status is PaperAspectStatus.succeeded
    assert result.full_text.status is PaperAspectStatus.succeeded
    assert fetch_calls == []
    assert cloud_calls == ["PMC5334499"]


def test_both_terminal_is_noop(session_factory: sessionmaker[Session]) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.unavailable,
    )
    fetch_calls: list[str] = []
    cloud_calls: list[str | None] = []

    result = fulfill_paper_metadata(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: fetch_calls.append("fetch")
        or mapped_photo(),
        enrich_from_pmc_cloud=lambda pmcid: cloud_calls.append(pmcid) or {},
    )

    assert result.source_record.status is PaperAspectStatus.succeeded
    assert result.full_text.status is PaperAspectStatus.unavailable
    assert fetch_calls == []
    assert cloud_calls == []


def test_source_then_full_text_when_no_pmcid(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(session_factory)
    cloud_calls: list[str | None] = []

    result = fulfill_paper_metadata(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: mapped_photo(),
        enrich_from_pmc_cloud=lambda pmcid: cloud_calls.append(pmcid) or cloud_hit(),
    )

    assert result.source_record.status is PaperAspectStatus.succeeded
    assert result.full_text.status is PaperAspectStatus.unavailable
    assert cloud_calls == []

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.title == "New title"
        assert paper.full_text_plain is None
    finally:
        session.close()


def test_source_then_cloud_hit(session_factory: sessionmaker[Session]) -> None:
    paper_id = create_test_paper(session_factory)
    payload = mapped_photo()
    payload["pmcid"] = "PMC5334499"

    result = fulfill_paper_metadata(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: payload,
        enrich_from_pmc_cloud=lambda _pmcid: cloud_hit(),
    )

    assert result.source_record.status is PaperAspectStatus.succeeded
    assert result.full_text.status is PaperAspectStatus.succeeded

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.full_text_plain == "Full article text from Cloud."
    finally:
        session.close()


def test_unsupported_source_leaves_full_text_not_started(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(session_factory, source_id="other", uid="9")
    cloud_calls: list[str | None] = []

    result = fulfill_paper_metadata(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: mapped_photo(),
        enrich_from_pmc_cloud=lambda pmcid: cloud_calls.append(pmcid) or cloud_hit(),
    )

    assert result.source_record.status is PaperAspectStatus.unavailable
    assert result.full_text.status is PaperAspectStatus.not_started
    assert cloud_calls == []


def test_failed_source_does_not_call_cloud(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper_id = create_test_paper(session_factory)
    cloud_calls: list[str | None] = []

    def fetch(_source_id: str, _source_uid: str) -> dict[str, Any]:
        raise RuntimeError("EFetch down")

    monkeypatch.setattr(
        "paper_reviewer.topic_brief_generation.fulfill_papers_metadata.inform.time.sleep",
        lambda _seconds: None,
    )

    result = fulfill_paper_metadata(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=fetch,
        enrich_from_pmc_cloud=lambda pmcid: cloud_calls.append(pmcid) or cloud_hit(),
    )

    assert result.source_record.status is PaperAspectStatus.failed
    assert result.full_text.status is PaperAspectStatus.not_started
    assert cloud_calls == []
