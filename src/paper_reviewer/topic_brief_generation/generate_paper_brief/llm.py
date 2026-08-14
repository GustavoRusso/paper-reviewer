"""Load the paper-brief template and call the production LLM."""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from paper_reviewer.schemas.topic_brief_generation.generate_paper_brief import (
    PaperBriefContent,
)

_TEMPLATE_PATH = Path(__file__).parent / "paper_brief_template.md"
_DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1"}
_PLACEHOLDER_API_KEY = "not-needed"
_GATEWAY_MAX_TOKENS = 4096
_ANSI_RE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\)|.)")
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL | re.IGNORECASE)


def resolve_openai_base_url(raw: str | None, *, in_container: bool) -> str | None:
    """Return a usable OpenAI-compatible base URL, or None for the public default.

    When the process runs in a container, rewrite loopback hosts to
    ``host.docker.internal`` so a gateway on the Docker host is reachable.
    """
    if raw is None:
        return None
    stripped = raw.strip()
    if not stripped:
        return None
    if not in_container:
        return stripped
    parsed = urlparse(stripped)
    if parsed.hostname not in _LOOPBACK_HOSTS:
        return stripped
    host = "host.docker.internal"
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    return urlunparse(parsed._replace(netloc=host))


def resolve_openai_model(raw: str | None) -> str | None:
    """Return a configured chat model id, or None when unset."""
    if raw is None:
        return None
    stripped = raw.strip()
    if not stripped:
        return None
    return stripped


def load_paper_brief_template() -> str:
    """Return the shared Markdown template (system prompt)."""
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


def template_field_ids() -> list[str]:
    """Return JSON field ids from the template YAML front matter, in order."""
    template = load_paper_brief_template()
    if not template.startswith("---"):
        raise ValueError("paper_brief_template.md is missing YAML front matter")
    end = template.find("\n---", 3)
    if end < 0:
        raise ValueError("paper_brief_template.md front matter is not closed")
    ids: list[str] = []
    for line in template[3:end].splitlines():
        stripped = line.strip()
        if stripped.startswith("- id:"):
            ids.append(stripped.split(":", 1)[1].strip())
    return ids


def build_brief_user_message(
    *,
    full_text_plain: str,
    title: str,
    journal: str | None,
    published_year: int | None,
) -> str:
    """Build the user message: bibliographic facts plus full text."""
    journal_display = journal if journal else "(unknown journal)"
    year_display = str(published_year) if published_year is not None else "(unknown year)"
    return (
        f"The archived paper is titled {title}, journal {journal_display}, "
        f"year {year_display}. Use these; do not replace them.\n\n"
        f"Article full text:\n{full_text_plain}"
    )


def parse_paper_brief_content(raw: str) -> PaperBriefContent:
    """Validate LLM text as PaperBriefContent.

    Public OpenAI structured output is already JSON. Local gateways may wrap
    JSON in Markdown, add extra keys, or leak ANSI control bytes.
    """
    cleaned = _strip_ansi_and_controls(raw)
    payload = _extract_json_object(cleaned)
    payload = _repair_unescaped_controls_in_strings(payload)
    return PaperBriefContent.model_validate_json(payload)


def _strip_ansi_and_controls(raw: str) -> str:
    text = _ANSI_RE.sub("", raw)
    return "".join(ch if ch in "\n\r\t" or ord(ch) >= 32 else "" for ch in text)


def _extract_json_object(text: str) -> str:
    stripped = text.strip()
    fenced = _JSON_FENCE_RE.search(stripped)
    if fenced:
        return fenced.group(1).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        return stripped[start : end + 1]
    raise ValueError("LLM returned no JSON object")


def _repair_unescaped_controls_in_strings(text: str) -> str:
    """Replace raw newlines inside JSON strings (llama.cpp line wrap)."""
    out: list[str] = []
    in_string = False
    escaped = False
    for ch in text:
        if in_string:
            if escaped:
                out.append(ch)
                escaped = False
                continue
            if ch == "\\":
                out.append(ch)
                escaped = True
                continue
            if ch == '"':
                out.append(ch)
                in_string = False
                continue
            if ch in "\n\r":
                out.append(" ")
                continue
            if ord(ch) < 32:
                continue
            out.append(ch)
            continue
        if ch == '"':
            in_string = True
        out.append(ch)
    return "".join(out)


def generate_paper_brief_content(
    full_text_plain: str,
    *,
    title: str,
    journal: str | None,
    published_year: int | None,
) -> PaperBriefContent:
    """Call chat completions and parse PaperBriefContent. Tests must inject a stub."""
    from openai import OpenAI
    from openai.lib._parsing import type_to_response_format_param

    api_key = os.environ.get("OPENAI_API_KEY") or None
    base_url = resolve_openai_base_url(
        os.environ.get("OPENAI_BASE_URL"),
        in_container=Path("/.dockerenv").exists(),
    )
    if not api_key:
        if base_url is None:
            raise ValueError("OPENAI_API_KEY is not set")
        api_key = _PLACEHOLDER_API_KEY
    model = resolve_openai_model(os.environ.get("OPENAI_MODEL"))
    if model is None:
        if base_url is not None:
            raise ValueError("OPENAI_MODEL is not set")
        model = _DEFAULT_OPENAI_MODEL
    if base_url is not None:
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=api_key)
    create_kwargs: dict[str, object] = {
        "model": model,
        "messages": [
            {"role": "system", "content": load_paper_brief_template()},
            {
                "role": "user",
                "content": build_brief_user_message(
                    full_text_plain=full_text_plain,
                    title=title,
                    journal=journal,
                    published_year=published_year,
                ),
            },
        ],
        "response_format": type_to_response_format_param(PaperBriefContent),
    }
    if base_url is not None:
        create_kwargs["max_tokens"] = _GATEWAY_MAX_TOKENS
    completion = client.chat.completions.create(**create_kwargs)
    content = completion.choices[0].message.content
    if not content:
        raise ValueError("OpenAI returned no parsed paper brief")
    return parse_paper_brief_content(content)
