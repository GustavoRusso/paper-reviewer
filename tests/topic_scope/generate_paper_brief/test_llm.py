"""Prompt builder for create_paper_brief: template file plus full text."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from paper_reviewer.topic_scope.generate_paper_brief.llm import (
    _call_and_log,
    _format_usage_log,
    _serialize_openai_part,
    build_brief_user_message,
    clip_full_text_for_gateway,
    extract_scientific_full_text,
    format_exception_message,
    generate_paper_brief_content,
    load_paper_brief_template,
    parse_paper_brief_content,
    resolve_gateway_max_tokens,
    resolve_openai_base_url,
    resolve_openai_model,
)
from tests.topic_scope.generate_paper_brief.helpers import sample_brief_content


def test_system_prompt_is_the_template_file() -> None:
    template = load_paper_brief_template()

    assert template.startswith("---")
    assert "Scientific paper brief template" in template
    assert "full_text_plain" in template
    assert "Do not use a research topic" in template


def test_user_message_includes_full_text_and_bibliographic_facts() -> None:
    user = build_brief_user_message(
        full_text_plain="UNIQUE_PLAIN_FULL_TEXT",
        title="Archived Title",
        journal="Eurosurveillance",
        published_year=2026,
    )

    assert "UNIQUE_PLAIN_FULL_TEXT" in user
    assert "Archived Title" in user
    assert "Eurosurveillance" in user
    assert "2026" in user
    assert "topic statement" not in user.lower()


def test_resolve_openai_base_url_unset_or_whitespace_is_none() -> None:
    assert resolve_openai_base_url(None, in_container=False) is None
    assert resolve_openai_base_url("", in_container=False) is None
    assert resolve_openai_base_url("   ", in_container=True) is None


def test_resolve_openai_base_url_localhost_unchanged_outside_container() -> None:
    assert (
        resolve_openai_base_url("http://localhost:11435/v1", in_container=False)
        == "http://localhost:11435/v1"
    )
    assert (
        resolve_openai_base_url("http://127.0.0.1:11435/v1", in_container=False)
        == "http://127.0.0.1:11435/v1"
    )


def test_resolve_openai_base_url_localhost_rewritten_in_container() -> None:
    assert (
        resolve_openai_base_url("http://localhost:11435/v1", in_container=True)
        == "http://host.docker.internal:11435/v1"
    )
    assert (
        resolve_openai_base_url("http://127.0.0.1:11435/v1", in_container=True)
        == "http://host.docker.internal:11435/v1"
    )


def test_resolve_openai_base_url_non_localhost_unchanged() -> None:
    url = "https://api.example.com/v1"
    assert resolve_openai_base_url(url, in_container=True) == url
    assert resolve_openai_base_url(url, in_container=False) == url


def _stub_openai(
    monkeypatch: pytest.MonkeyPatch,
    captured: dict[str, object],
    create_captured: dict[str, object] | None = None,
    *,
    content: str | None = None,
    reasoning: str | None = None,
    usage: object | None = None,
    finish_reason: str | None = "stop",
    responses: list[str] | None = None,
) -> dict[str, object]:
    """Stub openai.OpenAI.

    Returns a ``call_log`` dict with ``"call_count"`` (int) tracking how
    many times ``create()`` was called.

    When *responses* is set, each ``create()`` call pops the next element
    as the assistant ``content``.  After the list is exhausted the last
    element repeats.  *content* is ignored when *responses* is given.
    """
    parsed = sample_brief_content()
    default_raw = content if content is not None else parsed.model_dump_json()
    create_kwargs = create_captured if create_captured is not None else {}
    call_log: dict[str, object] = {"call_count": 0}
    response_queue: list[str] = list(responses) if responses else []

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            captured.clear()
            captured.update(kwargs)

            def create(**kw: object) -> object:
                create_kwargs.clear()
                create_kwargs.update(kw)
                call_log["call_count"] = int(call_log["call_count"]) + 1  # type: ignore[arg-type]
                if response_queue:
                    raw = response_queue.pop(0)
                else:
                    raw = default_raw
                message = SimpleNamespace(
                    role="assistant",
                    content=raw,
                    refusal=None,
                )
                if reasoning is not None:
                    message.reasoning = reasoning
                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=message,
                            finish_reason=finish_reason,
                        ),
                    ],
                    usage=usage,
                )

            self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr("openai.OpenAI", FakeClient)
    return call_log


def test_generate_paper_brief_content_uses_public_base_url_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert captured["base_url"] == "https://api.openai.com/v1"
    assert captured["api_key"] == "sk-test"


def test_generate_paper_brief_content_uses_public_base_url_when_env_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Compose may inject OPENAI_BASE_URL=""; SDK must not keep that empty URL."""
    captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured)
    monkeypatch.setenv("OPENAI_BASE_URL", "")

    generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert captured["base_url"] == "https://api.openai.com/v1"


def test_generate_paper_brief_content_passes_base_url_when_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "llama3.1-8b")

    generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert captured["base_url"] == "https://gateway.example/v1"


def test_generate_paper_brief_content_allows_empty_key_when_base_url_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "llama3.1-8b")

    generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert captured["base_url"] == "https://gateway.example/v1"
    assert captured["api_key"]


def test_generate_paper_brief_content_requires_key_without_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
        generate_paper_brief_content(
            "plain",
            title="Title",
            journal="Journal",
            published_year=2026,
        )


def test_resolve_openai_model_empty_is_none() -> None:
    assert resolve_openai_model(None) is None
    assert resolve_openai_model("") is None
    assert resolve_openai_model("   ") is None


def test_resolve_openai_model_uses_stripped_value() -> None:
    assert resolve_openai_model("gpt-4o-mini") == "gpt-4o-mini"
    assert resolve_openai_model("  llama3.1-8b  ") == "llama3.1-8b"


def test_generate_paper_brief_content_uses_code_default_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert create_captured["model"] == "gpt-4o-mini"


def test_serialize_openai_part_returns_raw_json() -> None:
    payload = SimpleNamespace(
        model_dump=lambda mode="json": {
            "role": "assistant",
            "content": '{"summary":"ok"}',
        }
    )

    dumped = _serialize_openai_part(payload)

    assert json.loads(dumped) == {
        "role": "assistant",
        "content": '{"summary":"ok"}',
    }


def test_format_usage_log_uses_prompt_and_completion_token_names() -> None:
    usage = SimpleNamespace(
        model_dump=lambda mode="json": {
            "prompt_tokens": 11,
            "completion_tokens": 7,
            "total_tokens": 18,
            "prompt_tokens_details": {"cached_tokens": 5},
        }
    )

    formatted = _format_usage_log(usage)
    labeled, _, raw = formatted.partition("OpenAI usage (raw JSON):")

    assert "prompt_tokens: 11" in labeled
    assert "completion_tokens: 7" in labeled
    assert "total_tokens: 18" in labeled
    assert "prompt_tokens_details:" in labeled
    assert '"cached_tokens": 5' in labeled
    assert "input_tokens:" not in labeled
    assert "output_tokens:" not in labeled
    assert '"cached_tokens": 5' in raw


def test_format_usage_log_accepts_input_and_output_names() -> None:
    usage = SimpleNamespace(
        model_dump=lambda mode="json": {
            "input_tokens": 13,
            "output_tokens": 9,
            "total_tokens": 22,
        }
    )

    formatted = _format_usage_log(usage)

    assert "input_tokens: 13" in formatted
    assert "output_tokens: 9" in formatted
    assert "total_tokens: 22" in formatted


def test_format_usage_log_handles_missing_usage() -> None:
    assert _format_usage_log(None) == "OpenAI usage: absent"


def test_generate_paper_brief_content_passes_configured_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)
    monkeypatch.setenv("OPENAI_MODEL", "llama3.1-8b")

    generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert create_captured["model"] == "llama3.1-8b"


def test_format_exception_message_includes_type_and_cause() -> None:
    try:
        raise OSError("Name or service not known")
    except OSError as cause:
        try:
            raise RuntimeError("Connection error.") from cause
        except RuntimeError as exc:
            message = format_exception_message(exc)

    assert message.startswith("RuntimeError: Connection error.")
    assert "(caused by: OSError: Name or service not known)" in message


def test_format_exception_message_without_cause() -> None:
    assert format_exception_message(RuntimeError("LLM timeout")) == (
        "RuntimeError: LLM timeout"
    )


def test_call_and_log_emits_error_and_reraises_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    emitted: list[tuple[bool, str]] = []

    def capture(message: str, *, error: bool = False) -> None:
        emitted.append((error, message))

    monkeypatch.setattr(
        "paper_reviewer.topic_scope.generate_paper_brief.llm._emit_openai_log",
        capture,
    )

    class BoomClient:
        base_url = "https://api.openai.com/v1/"

        def __init__(self) -> None:
            def create(**_kw: object) -> object:
                try:
                    raise OSError("getaddrinfo failed")
                except OSError as cause:
                    raise RuntimeError("Connection error.") from cause

            self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))

    with pytest.raises(RuntimeError, match="Connection error"):
        _call_and_log(BoomClient(), {"model": "gpt-4o-mini", "messages": []})

    assert len(emitted) == 2
    assert emitted[0][0] is False
    assert emitted[0][1].startswith("OpenAI request:\n")
    assert emitted[1][0] is True
    assert emitted[1][1].startswith("OpenAI call failed:\n")
    assert "base_url: https://api.openai.com/v1/" in emitted[1][1]
    assert "RuntimeError: Connection error." in emitted[1][1]
    assert "(caused by: OSError: getaddrinfo failed)" in emitted[1][1]


def test_generate_paper_brief_content_logs_request_response_and_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    usage = SimpleNamespace(
        model_dump=lambda mode="json": {
            "prompt_tokens": 21,
            "completion_tokens": 8,
            "total_tokens": 29,
            "completion_tokens_details": {"reasoning_tokens": 3},
        }
    )
    _stub_openai(monkeypatch, captured, create_captured, usage=usage)
    emitted: list[str] = []

    def capture(message: str, *, error: bool = False) -> None:
        assert error is False
        emitted.append(message)

    monkeypatch.setattr(
        "paper_reviewer.topic_scope.generate_paper_brief.llm._emit_openai_log",
        capture,
    )

    generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert len(emitted) == 3
    assert emitted[0].startswith("OpenAI request:\n")
    assert '"model": "gpt-4o-mini"' in emitted[0]
    assert emitted[1].startswith("OpenAI response message:\n")
    assert '"role": "assistant"' in emitted[1]
    assert emitted[2].startswith("OpenAI usage:\n")
    labeled, _, raw = emitted[2].partition("OpenAI usage (raw JSON):")
    assert "prompt_tokens: 21" in labeled
    assert "completion_tokens: 8" in labeled
    assert "total_tokens: 29" in labeled
    assert "completion_tokens_details:" in labeled
    assert '"reasoning_tokens": 3' in labeled
    assert "input_tokens:" not in labeled
    assert "output_tokens:" not in labeled
    assert '"reasoning_tokens": 3' in raw


def test_generate_paper_brief_content_returns_usage_integers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    usage = SimpleNamespace(
        model_dump=lambda mode="json": {
            "prompt_tokens": 21,
            "completion_tokens": 8,
            "total_tokens": 29,
            "completion_tokens_details": {"reasoning_tokens": 3},
        }
    )
    _stub_openai(monkeypatch, captured, usage=usage)

    result = generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert result.content.summary == sample_brief_content().summary
    assert result.prompt_tokens == 21
    assert result.completion_tokens == 8
    assert result.total_tokens == 29


def test_generate_paper_brief_content_returns_null_usage_when_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, usage=None)

    result = generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert result.content.summary == sample_brief_content().summary
    assert result.prompt_tokens is None
    assert result.completion_tokens is None
    assert result.total_tokens is None


def test_generate_paper_brief_content_does_not_map_input_output_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    usage = SimpleNamespace(
        model_dump=lambda mode="json": {
            "input_tokens": 13,
            "output_tokens": 9,
            "total_tokens": 22,
        }
    )
    _stub_openai(monkeypatch, captured, usage=usage)

    result = generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert result.prompt_tokens is None
    assert result.completion_tokens is None
    assert result.total_tokens == 22


def test_generate_paper_brief_content_requires_model_when_base_url_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    with pytest.raises(ValueError, match="OPENAI_MODEL is not set"):
        generate_paper_brief_content(
            "plain",
            title="Title",
            journal="Journal",
            published_year=2026,
        )


def test_generate_paper_brief_content_sends_json_schema_response_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)

    generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    response_format = create_captured["response_format"]
    assert isinstance(response_format, dict)
    assert response_format.get("type") == "json_schema"


def test_generate_paper_brief_content_omits_max_tokens_on_public_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert "max_tokens" not in create_captured
    assert "reasoning_effort" not in create_captured


def test_generate_paper_brief_content_sets_max_tokens_for_gateway(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "llama3.1-8b")

    generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert create_captured["max_tokens"] == 8192
    assert create_captured["reasoning_effort"] == "none"


def test_generate_paper_brief_content_parses_reasoning_when_content_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    brief = sample_brief_content()
    _stub_openai(
        monkeypatch,
        captured,
        content="",
        reasoning=brief.model_dump_json(),
    )
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gemma4:e4b")

    result = generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert result.content == brief


def test_generate_paper_brief_content_raises_when_content_and_reasoning_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, content="")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gemma4:e4b")

    with pytest.raises(ValueError, match="OpenAI returned no parsed paper brief"):
        generate_paper_brief_content(
            "plain",
            title="Title",
            journal="Journal",
            published_year=2026,
        )


def test_clip_full_text_for_gateway_keeps_prefix_and_drops_tail() -> None:
    body = "HEAD" + ("x" * 20_000) + "TAIL_UNIQUE"

    clipped = clip_full_text_for_gateway(body)

    assert clipped.startswith("HEAD")
    assert "TAIL_UNIQUE" not in clipped
    assert len(clipped) < len(body)
    assert "truncated" in clipped.lower()


def test_clip_full_text_for_gateway_keeps_short_text() -> None:
    assert clip_full_text_for_gateway("short body") == "short body"


def test_extract_scientific_full_text_keeps_scientific_sections() -> None:
    body = (
        "JOURNAL INFORMATION\n"
        "==============================\n"
        "BOILER_MARK affiliations and PMC converter.\n\n"
        "ABSTRACT\n\n"
        "ABSTRACT_MARK background and objectives.\n\n"
        "1 Introduction\n\n"
        "INTRO_MARK gap in knowledge.\n\n"
        "2 Materials and Methods\n\n"
        "METHODS_MARK RT-PCR and N = 12.\n"
        "2.1 Aim of the Study\n"
        "SUBMETHOD_MARK stays with methods.\n\n"
        "3 Results\n\n"
        "RESULTS_MARK 30 percent attack rate.\n\n"
        "Discussion\n\n"
        "DISCUSSION_MARK authors interpret findings.\n\n"
        "Funding\n\n"
        "FUNDING_MARK grant numbers.\n\n"
        "References\n\n"
        "REF_MARK Agliani et al. 2023.\n"
        + ("cite. " * 4000)
    )

    extracted = extract_scientific_full_text(body)

    assert "ABSTRACT_MARK" in extracted
    assert "INTRO_MARK" in extracted
    assert "METHODS_MARK" in extracted
    assert "SUBMETHOD_MARK" in extracted
    assert "RESULTS_MARK" in extracted
    assert "DISCUSSION_MARK" in extracted
    assert "BOILER_MARK" not in extracted
    assert "FUNDING_MARK" not in extracted
    assert "REF_MARK" not in extracted


def test_extract_scientific_full_text_keeps_long_introduction() -> None:
    intro = "INTRO_KEEP " + ("i" * 9000)
    body = (
        "ABSTRACT\n\nSHORT_ABS\n\n"
        f"1 Introduction\n\n{intro}\n\n"
        "3 Results\n\nRESULTS_KEEP\n\n"
        "References\n\nREF_ONLY\n"
    )

    extracted = extract_scientific_full_text(body)

    assert "SHORT_ABS" in extracted
    assert intro in extracted
    assert "RESULTS_KEEP" in extracted
    assert "REF_ONLY" not in extracted
    assert "truncated" not in extracted.lower()


def test_extract_scientific_full_text_keeps_unstructured() -> None:
    assert extract_scientific_full_text("short body") == "short body"


def test_clip_full_text_for_gateway_drops_references_even_when_short() -> None:
    body = (
        "ABSTRACT\n\nKeep abstract.\n\n"
        "3 Results\n\nKeep results.\n\n"
        "References\n\nDrop this citation list.\n"
    )

    clipped = clip_full_text_for_gateway(body)

    assert "Keep abstract" in clipped
    assert "Keep results" in clipped
    assert "Drop this citation" not in clipped


def test_clip_full_text_for_gateway_prefers_abstract_methods_results() -> None:
    intro = "INTRO_PAD " + ("i" * 9000)
    methods = "METHODS_KEEP " + ("m" * 2000)
    results = "RESULTS_KEEP " + ("r" * 2000)
    body = (
        "ABSTRACT\n\nSHORT_ABS\n\n"
        f"1 Introduction\n\n{intro}\n\n"
        f"2 Materials and Methods\n\n{methods}\n\n"
        f"3 Results\n\n{results}\n\n"
        "References\n\nREF_ONLY\n"
    )

    clipped = clip_full_text_for_gateway(body, max_chars=8000)

    assert "SHORT_ABS" in clipped
    assert "METHODS_KEEP" in clipped
    assert "RESULTS_KEEP" in clipped
    assert "REF_ONLY" not in clipped
    assert len(clipped) <= 8000


def test_generate_paper_brief_content_clips_full_text_on_gateway(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "llama3.1-8b")
    long_text = "START_MARK" + ("y" * 25_000) + "END_MARK"

    generate_paper_brief_content(
        long_text,
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    user = create_captured["messages"][1]["content"]
    assert "START_MARK" in user
    assert "END_MARK" not in user
    system = create_captured["messages"][0]["content"]
    assert "first non-whitespace character must be `{`" in system


def test_generate_paper_brief_content_keeps_full_text_on_public_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    long_text = "START_MARK" + ("y" * 25_000) + "END_MARK"

    generate_paper_brief_content(
        long_text,
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    user = create_captured["messages"][1]["content"]
    assert "START_MARK" in user
    assert "END_MARK" in user
    system = create_captured["messages"][0]["content"]
    assert "first non-whitespace character must be `{`" not in system


def test_generate_paper_brief_content_extracts_sections_on_public_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    generate_paper_brief_content(
        body,
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    user = create_captured["messages"][1]["content"]
    assert "SHORT_ABS" in user
    assert intro in user
    assert "METHODS_KEEP" in user
    assert "RESULTS_KEEP" in user
    assert "BOILER_MARK" not in user
    assert "REF_ONLY" not in user
    assert "truncated" not in user.lower()


def test_generate_paper_brief_content_parses_gateway_ansi_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    payload = sample_brief_content().model_dump_json()
    dirty = payload.replace("new result", "new result\x1b[K")
    _stub_openai(monkeypatch, captured, content=f"Sure.\n```json\n{dirty}\n```")

    result = generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert "new result" in result.content.summary
    assert "\x1b" not in result.content.summary


def test_parse_paper_brief_content_accepts_clean_json() -> None:
    payload = sample_brief_content().model_dump_json()

    parsed = parse_paper_brief_content(payload)

    assert parsed.summary == sample_brief_content().summary
    assert parsed.key_findings == sample_brief_content().key_findings


def test_parse_paper_brief_content_strips_ansi_and_markdown_fence() -> None:
    payload = sample_brief_content().model_dump_json()
    raw = f"Here you go:\n```json\n{payload.replace('gap.', 'gap.\x1b[K')}\n```\n"

    parsed = parse_paper_brief_content(raw)

    assert parsed.objective.endswith("gap.")


def test_parse_paper_brief_content_ignores_extra_keys() -> None:
    payload = sample_brief_content().model_dump(mode="json")
    payload["title"] = "Dummy Outbreak Report"
    payload["journal"] = "Test Journal"

    parsed = parse_paper_brief_content(json.dumps(payload))

    assert parsed.summary == sample_brief_content().summary
    assert parsed.objective == sample_brief_content().objective


def test_parse_paper_brief_content_repairs_newlines_inside_strings() -> None:
    raw = (
        "Here is the brief:\n```\n"
        '{\n  "summary": "A study reported a 30% attack rate \n'
        'during an outbreak in Lyon.",\n'
        '  "objective": "Investigate the outbreak.",\n'
        '  "key_findings": ["30% attack rate"]\n'
        "}\n```\n"
    )

    parsed = parse_paper_brief_content(raw)

    assert "30%" in parsed.summary
    assert "Lyon" in parsed.summary
    assert parsed.objective == "Investigate the outbreak."


@pytest.mark.parametrize(
    "illegal",
    [
        '{summary: "x"}',
        '["not", "an", "object"]',
    ],
)
def test_generate_paper_brief_content_includes_raw_assistant_on_parse_failure(
    monkeypatch: pytest.MonkeyPatch,
    illegal: str,
) -> None:
    captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, content=illegal)

    with pytest.raises(ValueError) as exc_info:
        generate_paper_brief_content(
            "plain",
            title="Title",
            journal="Journal",
            published_year=2026,
        )

    message = str(exc_info.value)
    assert illegal in message
    assert "Assistant output:" in message
    lowered = message.lower()
    assert (
        "json" in lowered
        or "validation" in lowered
        or "json object" in lowered
    )


def test_generate_paper_brief_content_caps_assistant_output_on_parse_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    illegal = "[" + ("x" * 9000) + "]"
    captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, content=illegal)

    with pytest.raises(ValueError) as exc_info:
        generate_paper_brief_content(
            "plain",
            title="Title",
            journal="Journal",
            published_year=2026,
        )

    message = str(exc_info.value)
    heading = "Assistant output:"
    dump = message[message.index(heading) + len(heading) :].lstrip("\n")
    assert dump == illegal[:8000]
    assert illegal[8000:] not in message


# --- resolve_gateway_max_tokens ---


def test_resolve_gateway_max_tokens_unset_returns_default() -> None:
    assert resolve_gateway_max_tokens(None) == 8192
    assert resolve_gateway_max_tokens("") == 8192
    assert resolve_gateway_max_tokens("   ") == 8192


def test_resolve_gateway_max_tokens_valid_integer() -> None:
    assert resolve_gateway_max_tokens("2048") == 2048
    assert resolve_gateway_max_tokens("  4096  ") == 4096


def test_resolve_gateway_max_tokens_invalid_raises() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        resolve_gateway_max_tokens("abc")
    with pytest.raises(ValueError, match="positive integer"):
        resolve_gateway_max_tokens("0")
    with pytest.raises(ValueError, match="positive integer"):
        resolve_gateway_max_tokens("-1")


def test_generate_paper_brief_content_uses_env_gateway_max_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "llama3.1-8b")
    monkeypatch.setenv("OPENAI_GATEWAY_MAX_TOKENS", "2048")

    generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert create_captured["max_tokens"] == 2048


# --- Gateway conciseness ---


def test_gateway_system_prompt_includes_conciseness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "llama3.1-8b")

    generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    system = create_captured["messages"][0]["content"]
    assert "prefer brevity" in system
    assert "no LaTeX" in system


def test_public_api_system_prompt_excludes_conciseness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, create_captured)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    system = create_captured["messages"][0]["content"]
    assert "prefer brevity" not in system
    assert "first non-whitespace character" not in system


# --- Retry logic ---


def test_retry_on_invalid_json_then_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    valid = sample_brief_content().model_dump_json()
    call_log = _stub_openai(
        monkeypatch, captured, responses=["NOT_JSON_AT_ALL", valid]
    )

    result = generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert call_log["call_count"] == 2
    assert result.content.summary == sample_brief_content().summary


def test_retry_on_finish_reason_length_then_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    truncated = '{"summary": "cut off here'
    valid = sample_brief_content().model_dump_json()
    call_log = _stub_openai(
        monkeypatch,
        captured,
        finish_reason="length",
        responses=[truncated, valid],
    )

    result = generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert call_log["call_count"] == 2
    assert result.content.summary == sample_brief_content().summary


def test_both_attempts_fail_raises_last_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    call_log = _stub_openai(
        monkeypatch, captured, responses=["BAD_1", "BAD_2"]
    )

    with pytest.raises(ValueError) as exc_info:
        generate_paper_brief_content(
            "plain",
            title="Title",
            journal="Journal",
            published_year=2026,
        )

    assert call_log["call_count"] == 2
    assert "BAD_2" in str(exc_info.value)


def test_first_attempt_succeeds_no_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    call_log = _stub_openai(monkeypatch, captured)

    result = generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert call_log["call_count"] == 1
    assert result.content.summary == sample_brief_content().summary


def test_retry_appends_retry_suffix_to_system_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    create_captured: dict[str, object] = {}
    valid = sample_brief_content().model_dump_json()
    _stub_openai(
        monkeypatch, captured, create_captured,
        responses=["NOT_JSON", valid],
    )

    generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    system = create_captured["messages"][0]["content"]
    assert "Previous response was truncated" in system


def test_empty_content_retries_then_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    call_log = _stub_openai(
        monkeypatch, captured, responses=["", ""]
    )

    with pytest.raises(ValueError, match="OpenAI returned no parsed paper brief"):
        generate_paper_brief_content(
            "plain",
            title="Title",
            journal="Journal",
            published_year=2026,
        )

    assert call_log["call_count"] == 2
