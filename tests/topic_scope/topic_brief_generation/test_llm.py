"""Topic brief LLM: user message, parse robustness, and OpenAI wiring."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

from paper_reviewer.schemas.topic_scope.topic_analysis import TopicFacet
from paper_reviewer.topic_scope.topic_brief_generation.briefed import (
    BriefedReference,
)
from paper_reviewer.topic_scope.topic_brief_generation.llm import (
    build_topic_brief_user_message,
    generate_topic_brief_content,
    parse_topic_brief_content,
)
from paper_reviewer.topic_scope.topic_brief_generation.template import (
    load_topic_brief_template,
)
from tests.topic_scope.topic_brief_generation.helpers import (
    sample_topic_brief_content,
)


def _briefed(
    *,
    doi: str = "10.1000/ex",
    title: str = "Example",
    pub_date: date | None = date(2024, 1, 1),
    summary: str = "Summary text",
) -> BriefedReference:
    return BriefedReference(
        reference_id=1,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        doi=doi,
        title=title,
        pub_date=pub_date,
        citation_description=f"{doi.upper()} — {title}",
        paper_brief_content={
            "summary": summary,
            "objective": "Objective",
            "key_findings": ["Finding"],
        },
    )


def test_system_prompt_is_the_template_file() -> None:
    template = load_topic_brief_template()

    assert template.startswith("---")
    assert "Topic brief template" in template
    assert "citation_description" in template


def test_user_message_includes_topic_facets_and_citation_description() -> None:
    user = build_topic_brief_user_message(
        topic_statement="glioblastoma immunotherapy",
        facets=[
            TopicFacet(
                id="disease",
                label="Disease",
                concepts=["glioblastoma"],
            )
        ],
        briefed_references=[
            _briefed(doi="10.1000/abc", title="Paper Title", summary="UNIQUE_SUMMARY")
        ],
    )

    assert "glioblastoma immunotherapy" in user
    assert "Disease" in user
    assert "glioblastoma" in user
    assert "10.1000/ABC — Paper Title" in user
    assert "UNIQUE_SUMMARY" in user
    assert "citation_description:" in user


def _stub_openai(
    monkeypatch: pytest.MonkeyPatch,
    captured: dict[str, object],
    create_captured: dict[str, object] | None = None,
    *,
    content: str | None = None,
) -> None:
    parsed = sample_topic_brief_content()
    raw = content if content is not None else parsed.model_dump_json()
    create_kwargs = create_captured if create_captured is not None else {}

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            captured.clear()
            captured.update(kwargs)

            def create(**kw: object) -> object:
                create_kwargs.clear()
                create_kwargs.update(kw)
                message = SimpleNamespace(content=raw)
                return SimpleNamespace(choices=[SimpleNamespace(message=message)])

            self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr("openai.OpenAI", FakeClient)


def test_generate_topic_brief_content_uses_template_as_system_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    generate_topic_brief_content(
        topic_statement="topic",
        facets=[],
        briefed_references=[_briefed()],
    )

    system = create_captured["messages"][0]["content"]
    assert "Topic brief template" in system
    user = create_captured["messages"][1]["content"]
    assert "topic" in user
    assert "10.1000/EX — Example" in user


def test_generate_topic_brief_content_requires_key_without_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
        generate_topic_brief_content(
            topic_statement="topic",
            facets=[],
            briefed_references=[_briefed()],
        )


def test_generate_topic_brief_content_adds_gateway_json_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "llama3.1-8b")

    generate_topic_brief_content(
        topic_statement="topic",
        facets=[],
        briefed_references=[_briefed()],
    )

    system = create_captured["messages"][0]["content"]
    assert "first non-whitespace character must be `{`" in system
    assert create_captured["max_tokens"] == 8192


def test_parse_topic_brief_content_accepts_clean_json() -> None:
    payload = sample_topic_brief_content().model_dump_json()

    parsed = parse_topic_brief_content(payload)

    assert parsed.title == sample_topic_brief_content().title


def test_parse_topic_brief_content_strips_ansi_and_markdown_fence() -> None:
    payload = sample_topic_brief_content().model_dump_json()
    raw = f"Here:\n```json\n{payload.replace('indexing', 'indexing\x1b[K')}\n```\n"

    parsed = parse_topic_brief_content(raw)

    assert "indexing" in parsed.title
    assert "\x1b" not in parsed.title


def test_parse_topic_brief_content_ignores_extra_keys() -> None:
    payload = sample_topic_brief_content().model_dump(mode="json")
    payload["extra_field"] = "ignore me"

    parsed = parse_topic_brief_content(json.dumps(payload))

    assert parsed.title == sample_topic_brief_content().title


@pytest.mark.parametrize(
    "illegal",
    [
        '{title: "x"}',
        '["not", "an", "object"]',
    ],
)
def test_generate_includes_raw_assistant_on_parse_failure(
    monkeypatch: pytest.MonkeyPatch,
    illegal: str,
) -> None:
    captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, content=illegal)

    with pytest.raises(ValueError) as exc_info:
        generate_topic_brief_content(
            topic_statement="topic",
            facets=[],
            briefed_references=[_briefed()],
        )

    message = str(exc_info.value)
    assert illegal in message
    assert "Assistant output:" in message


def test_generate_caps_assistant_output_on_parse_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    illegal = "[" + ("x" * 9000) + "]"
    captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, content=illegal)

    with pytest.raises(ValueError) as exc_info:
        generate_topic_brief_content(
            topic_statement="topic",
            facets=[],
            briefed_references=[_briefed()],
        )

    message = str(exc_info.value)
    heading = "Assistant output:"
    dump = message[message.index(heading) + len(heading) :].lstrip("\n")
    assert dump == illegal[:8000]
    assert illegal[8000:] not in message
