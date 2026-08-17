"""regenerate_paper flow: force source, force full text, then brief when succeeded."""

from __future__ import annotations

import importlib

import pytest
from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.flows.create_paper_brief import create_paper_brief
from paper_reviewer.flows.inform_full_text import inform_full_text
from paper_reviewer.flows.inform_source_record import inform_source_record
from paper_reviewer.flows.regenerate_paper import regenerate_paper
from paper_reviewer.models.paper import get_paper_by_id
from paper_reviewer.models.paper_brief import (
    get_paper_brief_by_paper_id,
)
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
import paper_reviewer.topic_scope.fulfill_papers_metadata.inform as inform_mod
import paper_reviewer.topic_scope.generate_paper_brief.create as create_mod
from tests.topic_scope.fulfill_papers_metadata.helpers import (
    cloud_hit,
    create_test_paper,
    mapped_photo,
)
from tests.topic_scope.generate_paper_brief.helpers import (
    add_brief,
    sample_brief_content,
)

_DOI = "10.1000/EXAMPLE"
_REGENERATE_MOD = importlib.import_module("paper_reviewer.flows.regenerate_paper")


def _patch_domain_defaults(
    monkeypatch: pytest.MonkeyPatch,
    session_factory: sessionmaker[Session],
    *,
    fetch_source_record,
    enrich_from_pmc_cloud,
    generate_content,
) -> None:
    monkeypatch.setattr(
        inform_mod,
        "_default_session_factory",
        lambda: session_factory,
    )
    monkeypatch.setattr(
        create_mod,
        "_default_session_factory",
        lambda: session_factory,
    )
    monkeypatch.setattr(
        inform_mod,
        "_default_fetch_source_record",
        fetch_source_record,
    )
    monkeypatch.setattr(
        inform_mod,
        "_default_enrich_from_pmc_cloud",
        enrich_from_pmc_cloud,
    )
    monkeypatch.setattr(
        create_mod,
        "_default_generate_content",
        generate_content,
    )
    monkeypatch.setattr(
        _REGENERATE_MOD,
        "inform_source_record",
        inform_source_record.fn,
    )
    monkeypatch.setattr(
        _REGENERATE_MOD,
        "inform_full_text",
        inform_full_text.fn,
    )
    monkeypatch.setattr(
        _REGENERATE_MOD,
        "create_paper_brief",
        create_paper_brief.fn,
    )


def test_force_unavailable_full_text_hit_rewrites_brief(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.unavailable,
        pmcid="PMC5334499",
    )
    add_brief(
        session_factory,
        paper_id,
        status=PaperAspectStatus.succeeded,
        content=sample_brief_content(summary="Old summary."),
    )
    fetch_calls: list[str] = []
    cloud_calls: list[str | None] = []
    payload = mapped_photo()
    payload["pmcid"] = "PMC5334499"

    _patch_domain_defaults(
        monkeypatch,
        session_factory,
        fetch_source_record=lambda _sid, _suid: fetch_calls.append("fetch")
        or payload,
        enrich_from_pmc_cloud=lambda pmcid: cloud_calls.append(pmcid) or cloud_hit(),
        generate_content=lambda *_a, **_k: sample_brief_content(summary="New summary."),
    )

    result = regenerate_paper.fn(paper_id, _DOI)

    assert result.paper_id == paper_id
    assert result.source_record.status is PaperAspectStatus.succeeded
    assert result.full_text.status is PaperAspectStatus.succeeded
    assert result.brief is not None
    assert result.brief.status is PaperAspectStatus.succeeded
    assert fetch_calls == ["fetch"]
    assert cloud_calls == ["PMC5334499"]

    session = session_factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        assert paper.title == "New title"
        assert paper.full_text_plain == "Full article text from Cloud."
        brief = get_paper_brief_by_paper_id(session, paper_id)
        assert brief is not None
        assert brief.content is not None
        assert brief.content["summary"] == "New summary."
    finally:
        session.close()


def test_force_full_text_still_unavailable_skips_brief(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.unavailable,
        pmcid="PMC5334499",
    )
    add_brief(
        session_factory,
        paper_id,
        status=PaperAspectStatus.succeeded,
        content=sample_brief_content(summary="Kept summary."),
    )
    llm_calls: list[str] = []

    _patch_domain_defaults(
        monkeypatch,
        session_factory,
        fetch_source_record=lambda _sid, _suid: mapped_photo(),
        enrich_from_pmc_cloud=lambda _pmcid: {},
        generate_content=lambda *_a, **_k: llm_calls.append("llm")
        or sample_brief_content(),
    )

    result = regenerate_paper.fn(paper_id, _DOI)

    assert result.full_text.status is PaperAspectStatus.unavailable
    assert result.brief is None
    assert llm_calls == []

    session = session_factory()
    try:
        brief = get_paper_brief_by_paper_id(session, paper_id)
        assert brief is not None
        assert brief.content is not None
        assert brief.content["summary"] == "Kept summary."
        assert brief.status is PaperAspectStatus.succeeded
    finally:
        session.close()
