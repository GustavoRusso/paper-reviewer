"""regenerate_paper: force source, force full text, then brief when succeeded."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.topic_brief_generation import get_paper_by_id
from paper_reviewer.models.topic_brief_generation.paper_brief import (
    get_paper_brief_by_paper_id,
)
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.topic_brief_generation.fulfill_papers_metadata import (
    fulfill_paper_metadata,
    regenerate_paper,
)
from tests.topic_brief_generation.fulfill_papers_metadata.helpers import (
    cloud_hit,
    create_test_paper,
    mapped_photo,
)
from tests.topic_brief_generation.generate_paper_brief.helpers import (
    add_brief,
    sample_brief_content,
)


def test_force_unavailable_full_text_hit_rewrites_brief(
    session_factory: sessionmaker[Session],
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

    result = regenerate_paper(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: fetch_calls.append("fetch") or payload,
        enrich_from_pmc_cloud=lambda pmcid: cloud_calls.append(pmcid) or cloud_hit(),
        generate_content=lambda *_a, **_k: sample_brief_content(summary="New summary."),
    )

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

    result = regenerate_paper(
        paper_id,
        session_factory=session_factory,
        fetch_source_record=lambda _sid, _suid: mapped_photo(),
        enrich_from_pmc_cloud=lambda _pmcid: {},
        generate_content=lambda *_a, **_k: llm_calls.append("llm")
        or sample_brief_content(),
    )

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


def test_fulfill_paper_metadata_does_not_force(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        source_record_status=PaperAspectStatus.succeeded,
        full_text_status=PaperAspectStatus.unavailable,
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

    assert result.source_record.status is PaperAspectStatus.succeeded
    assert result.full_text.status is PaperAspectStatus.unavailable
    assert fetch_calls == []
    assert cloud_calls == []
