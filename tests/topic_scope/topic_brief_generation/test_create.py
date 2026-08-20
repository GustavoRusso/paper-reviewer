"""create_topic_brief: briefed gate, overwrite, and stub LLM writes."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.topic_scope.topic_analysis import TopicFacet
from paper_reviewer.models.topic_scope.topic_brief import (
    create_topic_brief_row,
    get_topic_brief_by_topic_scope_id,
)
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.topic_analysis import TopicFacet as TopicFacetSchema
from paper_reviewer.schemas.topic_scope.topic_brief_generation import (
    TopicBriefContent,
    TopicBriefLlmResult,
)
from paper_reviewer.topic_scope.topic_brief_generation import create_topic_brief
from paper_reviewer.topic_scope.topic_brief_generation.briefed import (
    BriefedReference,
)
from paper_reviewer.topic_scope.topic_brief_generation.create import (
    ZERO_BRIEFED_ERROR,
)
from tests.topic_scope.topic_brief_generation.helpers import (
    add_briefed_reference,
    create_test_scope,
    sample_llm_result,
    sample_topic_brief_content,
)


def test_creates_succeeded_when_briefed_and_no_row(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    add_briefed_reference(session_factory, topic_scope_id)
    calls: list[str] = []

    def generate(
        *,
        topic_statement: str,
        facets: object,
        briefed_references: object,
    ) -> TopicBriefLlmResult:
        calls.append(topic_statement)
        return sample_llm_result(
            sample_topic_brief_content(title="Drafted title for this topic"),
            prompt_tokens=21,
            completion_tokens=8,
            total_tokens=29,
        )

    result = create_topic_brief(
        topic_scope_id,
        session_factory=session_factory,
        generate_content=generate,
    )

    assert result.status is PaperAspectStatus.succeeded
    assert result.error_message is None
    assert calls == ["glioblastoma immunotherapy"]

    session = session_factory()
    try:
        brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
        assert brief is not None
        assert brief.content is not None
        assert brief.content["title"] == "Drafted title for this topic"
        assert brief.prompt_tokens == 21
        assert brief.completion_tokens == 8
        assert brief.total_tokens == 29
    finally:
        session.close()


def test_force_rewrites_succeeded_content(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    add_briefed_reference(session_factory, topic_scope_id)
    session = session_factory()
    try:
        row = create_topic_brief_row(session, topic_scope_id=topic_scope_id)
        row.status = PaperAspectStatus.succeeded
        row.content = sample_topic_brief_content(title="Old title").model_dump(
            mode="json"
        )
        row.prompt_tokens = 11
        row.completion_tokens = 7
        row.total_tokens = 18
        session.commit()
    finally:
        session.close()

    result = create_topic_brief(
        topic_scope_id,
        force=True,
        session_factory=session_factory,
        generate_content=lambda **_k: sample_llm_result(
            sample_topic_brief_content(title="New title after rewrite"),
            prompt_tokens=40,
            completion_tokens=12,
            total_tokens=52,
        ),
    )

    assert result.status is PaperAspectStatus.succeeded
    session = session_factory()
    try:
        brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
        assert brief is not None
        assert brief.content is not None
        assert brief.content["title"] == "New title after rewrite"
        assert brief.prompt_tokens == 40
        assert brief.completion_tokens == 12
        assert brief.total_tokens == 52
    finally:
        session.close()


def test_force_false_skips_when_succeeded(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    add_briefed_reference(session_factory, topic_scope_id)
    session = session_factory()
    try:
        row = create_topic_brief_row(session, topic_scope_id=topic_scope_id)
        row.status = PaperAspectStatus.succeeded
        row.content = sample_topic_brief_content(title="Keep me").model_dump(
            mode="json"
        )
        row.prompt_tokens = 11
        row.completion_tokens = 7
        row.total_tokens = 18
        session.commit()
    finally:
        session.close()
    calls: list[str] = []

    result = create_topic_brief(
        topic_scope_id,
        force=False,
        session_factory=session_factory,
        generate_content=lambda **_k: calls.append("llm")
        or sample_topic_brief_content(),
    )

    assert result.status is PaperAspectStatus.succeeded
    assert calls == []

    session = session_factory()
    try:
        brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
        assert brief is not None
        assert brief.content is not None
        assert brief.content["title"] == "Keep me"
        assert brief.prompt_tokens == 11
        assert brief.completion_tokens == 7
        assert brief.total_tokens == 18
    finally:
        session.close()


def test_zero_briefed_fails_without_llm_and_keeps_prior_content(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    session = session_factory()
    try:
        row = create_topic_brief_row(session, topic_scope_id=topic_scope_id)
        row.status = PaperAspectStatus.succeeded
        row.content = sample_topic_brief_content(title="Prior good").model_dump(
            mode="json"
        )
        row.prompt_tokens = 11
        row.completion_tokens = 7
        row.total_tokens = 18
        session.commit()
    finally:
        session.close()
    calls: list[str] = []

    result = create_topic_brief(
        topic_scope_id,
        session_factory=session_factory,
        generate_content=lambda **_k: calls.append("llm")
        or sample_topic_brief_content(),
    )

    assert result.status is PaperAspectStatus.failed
    assert result.error_message == ZERO_BRIEFED_ERROR
    assert calls == []

    session = session_factory()
    try:
        brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
        assert brief is not None
        assert brief.content is not None
        assert brief.content["title"] == "Prior good"
        assert brief.prompt_tokens == 11
        assert brief.completion_tokens == 7
        assert brief.total_tokens == 18
    finally:
        session.close()


def test_llm_failure_keeps_prior_content(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    add_briefed_reference(session_factory, topic_scope_id)
    session = session_factory()
    try:
        row = create_topic_brief_row(session, topic_scope_id=topic_scope_id)
        row.status = PaperAspectStatus.succeeded
        row.content = sample_topic_brief_content(title="Prior good").model_dump(
            mode="json"
        )
        row.prompt_tokens = 11
        row.completion_tokens = 7
        row.total_tokens = 18
        session.commit()
    finally:
        session.close()

    def boom(**_kwargs: object) -> TopicBriefContent:
        raise RuntimeError("llm down")

    result = create_topic_brief(
        topic_scope_id,
        session_factory=session_factory,
        generate_content=boom,
    )

    assert result.status is PaperAspectStatus.failed
    assert result.error_message == "RuntimeError: llm down"

    session = session_factory()
    try:
        brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
        assert brief is not None
        assert brief.content is not None
        assert brief.content["title"] == "Prior good"
        assert brief.prompt_tokens == 11
        assert brief.completion_tokens == 7
        assert brief.total_tokens == 18
    finally:
        session.close()


def test_generator_receives_ordered_briefed_payload_with_citation_description(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    session = session_factory()
    try:
        session.add(
            TopicFacet(
                topic_scope_id=topic_scope_id,
                facet_id="disease",
                label="Disease",
                intent="focus",
                concepts=["glioblastoma"],
                synonyms=[],
                filters={},
                position=0,
            )
        )
        session.commit()
    finally:
        session.close()

    add_briefed_reference(
        session_factory,
        topic_scope_id,
        uid="1",
        doi="10.1000/old",
        title="Older paper",
        pub_date=date(2020, 1, 1),
        brief_content={
            "summary": "Old summary",
            "objective": "o",
            "key_findings": ["a"],
        },
    )
    add_briefed_reference(
        session_factory,
        topic_scope_id,
        uid="2",
        doi="10.1000/new",
        title="Newer paper",
        pub_date=date(2024, 6, 1),
        brief_content={
            "summary": "New summary",
            "objective": "o",
            "key_findings": ["b"],
        },
    )
    add_briefed_reference(
        session_factory,
        topic_scope_id,
        uid="3",
        doi="10.1000/null",
        title="No date paper",
        pub_date=None,
        brief_content={
            "summary": "Null summary",
            "objective": "o",
            "key_findings": ["c"],
        },
    )

    captured: dict[str, object] = {}

    def generate(
        *,
        topic_statement: str,
        facets: list[TopicFacetSchema],
        briefed_references: list[BriefedReference],
    ) -> TopicBriefContent:
        captured["topic_statement"] = topic_statement
        captured["facets"] = facets
        captured["briefed"] = briefed_references
        return sample_topic_brief_content()

    result = create_topic_brief(
        topic_scope_id,
        session_factory=session_factory,
        generate_content=generate,
    )

    assert result.status is PaperAspectStatus.succeeded
    assert captured["topic_statement"] == "glioblastoma immunotherapy"
    facets = captured["facets"]
    assert isinstance(facets, list)
    assert len(facets) == 1
    assert facets[0].id == "disease"
    assert facets[0].concepts == ["glioblastoma"]

    briefed = captured["briefed"]
    assert isinstance(briefed, list)
    assert [item.doi for item in briefed] == [
        "10.1000/new",
        "10.1000/old",
        "10.1000/null",
    ]
    assert briefed[0].citation_description == "10.1000/NEW — Newer paper"
    assert briefed[1].citation_description == "10.1000/OLD — Older paper"
    assert briefed[0].paper_brief_content["summary"] == "New summary"


def test_parse_failure_message_is_persisted_with_assistant_dump(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    add_briefed_reference(session_factory, topic_scope_id)

    def boom(**_kwargs: object) -> TopicBriefContent:
        raise ValueError(
            "LLM returned no JSON object\n\nAssistant output:\n{not-json}"
        )

    result = create_topic_brief(
        topic_scope_id,
        session_factory=session_factory,
        generate_content=boom,
    )

    assert result.status is PaperAspectStatus.failed
    assert result.error_message is not None
    assert "Assistant output:" in result.error_message
    assert "{not-json}" in result.error_message


def test_missing_usage_stores_null_and_succeeds(
    session_factory: sessionmaker[Session],
) -> None:
    topic_scope_id = create_test_scope(session_factory)
    add_briefed_reference(session_factory, topic_scope_id)

    result = create_topic_brief(
        topic_scope_id,
        session_factory=session_factory,
        generate_content=lambda **_k: sample_llm_result(
            sample_topic_brief_content(title="No usage."),
        ),
    )

    assert result.status is PaperAspectStatus.succeeded
    session = session_factory()
    try:
        brief = get_topic_brief_by_topic_scope_id(session, topic_scope_id)
        assert brief is not None
        assert brief.content is not None
        assert brief.content["title"] == "No usage."
        assert brief.prompt_tokens is None
        assert brief.completion_tokens is None
        assert brief.total_tokens is None
    finally:
        session.close()
