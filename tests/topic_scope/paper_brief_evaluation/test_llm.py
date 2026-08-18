"""Judge prompt and OpenAI call for evaluate_paper_brief. No live network."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from paper_reviewer.topic_scope.generate_paper_brief.llm import (
    template_field_contract,
)
from paper_reviewer.topic_scope.paper_brief_evaluation.llm import (
    build_evaluation_user_message,
    evaluation_criterion_ids,
    judge_paper_brief_evaluation,
    load_paper_brief_evaluation_template,
)
from tests.topic_scope.generate_paper_brief.helpers import sample_brief_content
from tests.topic_scope.paper_brief_evaluation.helpers import sample_evaluation


def test_system_prompt_is_the_evaluation_template_file() -> None:
    template = load_paper_brief_evaluation_template()

    assert template.startswith("---")
    assert "faithfulness" in template
    assert "completeness" in template
    assert "conciseness" in template
    assert "topic_agnostic" in template
    assert "Do not return evaluation_score" in template


def test_evaluation_criterion_ids_match_template_front_matter() -> None:
    assert evaluation_criterion_ids() == [
        "faithfulness",
        "completeness",
        "conciseness",
        "topic_agnostic",
    ]


def test_user_message_includes_brief_json_full_text_and_field_contract() -> None:
    content = sample_brief_content(summary="Grounded takeaway.")

    user = build_evaluation_user_message(
        full_text_plain="UNIQUE_PLAIN_FULL_TEXT",
        content=content,
    )

    assert "UNIQUE_PLAIN_FULL_TEXT" in user
    assert "Grounded takeaway." in user
    assert '"summary"' in user
    assert "topic statement" not in user.lower()
    assert "topic facet" not in user.lower()
    for field_id, required in template_field_contract():
        flag = "required" if required else "optional"
        assert f"{field_id}: {flag}" in user


def _stub_openai(
    monkeypatch: pytest.MonkeyPatch,
    captured: dict[str, object],
    create_captured: dict[str, object] | None = None,
    *,
    content: str | None = None,
    reasoning: str | None = None,
) -> None:
    parsed = sample_evaluation()
    raw = content if content is not None else parsed.model_dump_json()
    create_kwargs = create_captured if create_captured is not None else {}

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            captured.clear()
            captured.update(kwargs)

            def create(**kw: object) -> object:
                create_kwargs.clear()
                create_kwargs.update(kw)
                message = SimpleNamespace(
                    role="assistant",
                    content=raw,
                    refusal=None,
                )
                if reasoning is not None:
                    message.reasoning = reasoning
                return SimpleNamespace(
                    choices=[SimpleNamespace(message=message)],
                    usage=None,
                )

            self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr("openai.OpenAI", FakeClient)


def test_judge_sends_json_schema_response_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)

    judge_paper_brief_evaluation(
        "plain",
        content=sample_brief_content(),
    )

    response_format = create_captured["response_format"]
    assert isinstance(response_format, dict)
    assert response_format.get("type") == "json_schema"
    assert "evaluation_score" not in json.dumps(response_format)


def test_judge_sets_temperature_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)

    judge_paper_brief_evaluation(
        "plain",
        content=sample_brief_content(),
    )

    assert create_captured["temperature"] == 0


def test_judge_extracts_sections_on_public_api(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    intro = "INTRO_KEEP " + ("i" * 9000)
    body = (
        "JOURNAL INFORMATION\nBOILER_MARK\n\n"
        "ABSTRACT\n\nSHORT_ABS\n\n"
        f"1 Introduction\n\n{intro}\n\n"
        "2 Materials and Methods\n\nMETHODS_KEEP\n\n"
        "3 Results\n\nRESULTS_KEEP\n\n"
        "References\n\nREF_ONLY\n"
    )

    judge_paper_brief_evaluation(
        body,
        content=sample_brief_content(),
    )

    user = create_captured["messages"][1]["content"]
    assert "SHORT_ABS" in user
    assert intro in user
    assert "METHODS_KEEP" in user
    assert "RESULTS_KEEP" in user
    assert "BOILER_MARK" not in user
    assert "REF_ONLY" not in user
    assert "truncated" not in user.lower()


def test_judge_clips_full_text_on_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "llama3.1-8b")
    long_text = "START_MARK" + ("y" * 25_000) + "END_MARK"

    judge_paper_brief_evaluation(
        long_text,
        content=sample_brief_content(),
    )

    user = create_captured["messages"][1]["content"]
    assert "START_MARK" in user
    assert "END_MARK" not in user
    system = create_captured["messages"][0]["content"]
    assert "first non-whitespace character must be `{`" in system


def test_judge_omits_gateway_options_on_public_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    judge_paper_brief_evaluation(
        "plain",
        content=sample_brief_content(),
    )

    assert "max_tokens" not in create_captured
    assert "reasoning_effort" not in create_captured


def test_judge_sets_gateway_chat_options(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "llama3.1-8b")

    judge_paper_brief_evaluation(
        "plain",
        content=sample_brief_content(),
    )

    assert create_captured["max_tokens"] == 4096
    assert create_captured["reasoning_effort"] == "none"


def test_judge_parses_reasoning_when_content_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    evaluation = sample_evaluation()
    _stub_openai(
        monkeypatch,
        captured,
        content="",
        reasoning=evaluation.model_dump_json(),
    )
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gemma4:e4b")

    result = judge_paper_brief_evaluation(
        "plain",
        content=sample_brief_content(),
    )

    assert result == evaluation


def test_judge_raises_when_content_and_reasoning_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, content="")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gemma4:e4b")

    with pytest.raises(
        ValueError, match="OpenAI returned no parsed paper brief evaluation"
    ):
        judge_paper_brief_evaluation(
            "plain",
            content=sample_brief_content(),
        )


@pytest.mark.parametrize(
    "illegal",
    [
        '{summary: "x"}',
        '["not", "an", "object"]',
    ],
)
def test_judge_includes_raw_assistant_on_parse_failure(
    monkeypatch: pytest.MonkeyPatch,
    illegal: str,
) -> None:
    captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, content=illegal)

    with pytest.raises(ValueError) as exc_info:
        judge_paper_brief_evaluation(
            "plain",
            content=sample_brief_content(),
        )

    message = str(exc_info.value)
    assert illegal in message
    assert "Assistant output:" in message


def test_judge_caps_assistant_output_on_parse_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    illegal = "[" + ("x" * 9000) + "]"
    captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, content=illegal)

    with pytest.raises(ValueError) as exc_info:
        judge_paper_brief_evaluation(
            "plain",
            content=sample_brief_content(),
        )

    message = str(exc_info.value)
    heading = "Assistant output:"
    dump = message[message.index(heading) + len(heading) :].lstrip("\n")
    assert dump == illegal[:8000]
    assert illegal[8000:] not in message
