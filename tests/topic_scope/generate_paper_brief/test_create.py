"""create_paper_brief: default skip, full-text gate, and LLM writes."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.paper_brief import (
    get_paper_brief_by_paper_id,
)
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    PaperBriefContent,
)
from paper_reviewer.topic_scope.generate_paper_brief import create_paper_brief
from tests.topic_scope.generate_paper_brief.helpers import (
    add_brief,
    create_test_paper,
    sample_brief_content,
)


def test_skips_llm_when_brief_succeeded_and_force_false(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(session_factory)
    original = sample_brief_content(summary="Already done.")
    add_brief(
        session_factory,
        paper_id,
        status=PaperAspectStatus.succeeded,
        content=original,
    )
    calls: list[str] = []

    def generate(
        full_text_plain: str,
        *,
        title: str,
        journal: str | None,
        published_year: int | None,
    ) -> PaperBriefContent:
        calls.append(full_text_plain)
        return sample_brief_content(summary="Rewritten.")

    result = create_paper_brief(
        paper_id,
        session_factory=session_factory,
        generate_content=generate,
    )

    assert result.status is PaperAspectStatus.succeeded
    assert result.error_message is None
    assert calls == []

    session = session_factory()
    try:
        brief = get_paper_brief_by_paper_id(session, paper_id)
        assert brief is not None
        assert brief.content is not None
        assert brief.content["summary"] == "Already done."
    finally:
        session.close()


def test_skips_llm_when_brief_failed_and_force_false(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(session_factory)
    add_brief(
        session_factory,
        paper_id,
        status=PaperAspectStatus.failed,
        error_message="prior failure",
    )
    calls: list[str] = []

    result = create_paper_brief(
        paper_id,
        session_factory=session_factory,
        generate_content=lambda *_a, **_k: calls.append("llm") or sample_brief_content(),
    )

    assert result.status is PaperAspectStatus.failed
    assert result.error_message == "prior failure"
    assert calls == []


def test_does_not_write_succeeded_when_full_text_not_succeeded(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        full_text_status=PaperAspectStatus.unavailable,
        full_text_plain=None,
    )
    calls: list[str] = []

    result = create_paper_brief(
        paper_id,
        session_factory=session_factory,
        generate_content=lambda *_a, **_k: calls.append("llm") or sample_brief_content(),
    )

    assert result.status is not PaperAspectStatus.succeeded
    assert calls == []

    session = session_factory()
    try:
        brief = get_paper_brief_by_paper_id(session, paper_id)
        assert brief is None or brief.status is not PaperAspectStatus.succeeded
    finally:
        session.close()


def test_happy_path_stores_content_and_passes_full_text(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        full_text_plain="UNIQUE_FULL_TEXT_BODY",
        title="Archived Title",
        journal="Eurosurveillance",
        published_year=2026,
    )
    seen: dict[str, object] = {}

    def generate(
        full_text_plain: str,
        *,
        title: str,
        journal: str | None,
        published_year: int | None,
    ) -> PaperBriefContent:
        seen["full_text"] = full_text_plain
        seen["title"] = title
        seen["journal"] = journal
        seen["year"] = published_year
        return sample_brief_content(
            summary="Grounded takeaway.",
            key_findings=["N = 450 confirmed cases"],
        )

    result = create_paper_brief(
        paper_id,
        session_factory=session_factory,
        generate_content=generate,
    )

    assert result.status is PaperAspectStatus.succeeded
    assert result.error_message is None
    assert seen["full_text"] == "UNIQUE_FULL_TEXT_BODY"
    assert seen["title"] == "Archived Title"
    assert seen["journal"] == "Eurosurveillance"
    assert seen["year"] == 2026

    session = session_factory()
    try:
        brief = get_paper_brief_by_paper_id(session, paper_id)
        assert brief is not None
        assert brief.status is PaperAspectStatus.succeeded
        assert brief.error_message is None
        assert brief.content is not None
        assert brief.content["summary"] == "Grounded takeaway."
        assert brief.content["key_findings"] == ["N = 450 confirmed cases"]
        assert "relevance_to_topic" not in brief.content
    finally:
        session.close()


def test_force_true_rewrites_succeeded_brief(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(session_factory)
    add_brief(
        session_factory,
        paper_id,
        status=PaperAspectStatus.succeeded,
        content=sample_brief_content(summary="Old summary."),
    )

    result = create_paper_brief(
        paper_id,
        force=True,
        session_factory=session_factory,
        generate_content=lambda *_a, **_k: sample_brief_content(summary="New summary."),
    )

    assert result.status is PaperAspectStatus.succeeded

    session = session_factory()
    try:
        brief = get_paper_brief_by_paper_id(session, paper_id)
        assert brief is not None
        assert brief.content is not None
        assert brief.content["summary"] == "New summary."
    finally:
        session.close()


def test_license_stub_full_text_does_not_call_llm(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(
        session_factory,
        full_text_status=PaperAspectStatus.succeeded,
        full_text_plain=(
            "Abstract\n\n"
            "Orthoflaviviruses depend on host metabolic resources.\n\n"
            "Full Text Availability\n\n"
            "The license terms selected by the author(s) for this preprint "
            "version do not permit archiving in PMC. The full text is "
            "available from the preprint server.\n"
        ),
    )
    calls: list[str] = []

    result = create_paper_brief(
        paper_id,
        session_factory=session_factory,
        generate_content=lambda *_a, **_k: calls.append("llm") or sample_brief_content(),
    )

    assert result.status is PaperAspectStatus.failed
    assert result.error_message == "full_text_plain is not usable article body"
    assert calls == []

    session = session_factory()
    try:
        brief = get_paper_brief_by_paper_id(session, paper_id)
        assert brief is not None
        assert brief.status is PaperAspectStatus.failed
        assert brief.content is None
        assert brief.error_message == "full_text_plain is not usable article body"
    finally:
        session.close()


def test_llm_failure_sets_failed_with_message(
    session_factory: sessionmaker[Session],
) -> None:
    paper_id = create_test_paper(session_factory)

    def generate(
        full_text_plain: str,
        *,
        title: str,
        journal: str | None,
        published_year: int | None,
    ) -> PaperBriefContent:
        raise RuntimeError("LLM timeout")

    result = create_paper_brief(
        paper_id,
        session_factory=session_factory,
        generate_content=generate,
    )

    assert result.status is PaperAspectStatus.failed
    assert result.error_message is not None
    assert "LLM timeout" in result.error_message

    session = session_factory()
    try:
        brief = get_paper_brief_by_paper_id(session, paper_id)
        assert brief is not None
        assert brief.status is PaperAspectStatus.failed
        assert brief.content is None
    finally:
        session.close()
