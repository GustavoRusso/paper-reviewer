"""Prompt builder for create_paper_brief: template file plus full text."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from paper_reviewer.topic_brief_generation.generate_paper_brief.llm import (
    build_brief_user_message,
    generate_paper_brief_content,
    load_paper_brief_template,
    resolve_openai_base_url,
    resolve_openai_model,
)
from tests.topic_brief_generation.generate_paper_brief.helpers import sample_brief_content


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
    parse_captured: dict[str, object] | None = None,
) -> None:
    parsed = sample_brief_content()
    parse_kwargs = parse_captured if parse_captured is not None else {}

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            captured.clear()
            captured.update(kwargs)
            message = SimpleNamespace(parsed=parsed)
            completion = SimpleNamespace(choices=[SimpleNamespace(message=message)])

            def parse(**kw: object) -> object:
                parse_kwargs.clear()
                parse_kwargs.update(kw)
                return completion

            self.chat = SimpleNamespace(completions=SimpleNamespace(parse=parse))

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr("openai.OpenAI", FakeClient)


def test_generate_paper_brief_content_omits_base_url_when_unset(
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

    assert "base_url" not in captured
    assert captured["api_key"] == "sk-test"


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
    parse_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, parse_captured)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert parse_captured["model"] == "gpt-4o-mini"


def test_generate_paper_brief_content_passes_configured_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    parse_captured: dict[str, object] = {}
    _stub_openai(monkeypatch, captured, parse_captured)
    monkeypatch.setenv("OPENAI_MODEL", "llama3.1-8b")

    generate_paper_brief_content(
        "plain",
        title="Title",
        journal="Journal",
        published_year=2026,
    )

    assert parse_captured["model"] == "llama3.1-8b"


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
