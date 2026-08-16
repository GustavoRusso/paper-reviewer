"""Load the topic-brief template and call the production LLM."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from paper_reviewer.schemas.topic_scope.topic_analysis import TopicFacet
from paper_reviewer.schemas.topic_scope.topic_brief_generation import (
    TopicBriefContent,
)
from paper_reviewer.topic_scope.generate_paper_brief.llm import (
    resolve_openai_base_url,
    resolve_openai_model,
)
from paper_reviewer.topic_scope.topic_brief_generation.briefed import (
    BriefedReference,
)
from paper_reviewer.topic_scope.topic_brief_generation.template import (
    load_topic_brief_template,
)

_DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
_PLACEHOLDER_API_KEY = "not-needed"
_GATEWAY_MAX_TOKENS = 8192
_GATEWAY_JSON_ONLY = (
    "Reply with a single JSON object only. "
    "The first non-whitespace character must be `{`."
)
_ASSISTANT_OUTPUT_HEADING = "Assistant output:"
_ASSISTANT_OUTPUT_MAX_CHARS = 8000
_ANSI_RE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\)|.)")
_JSON_FENCE_RE = re.compile(
    r"```(?:json)?\s*(\{.*\})\s*```",
    re.DOTALL | re.IGNORECASE,
)


def build_topic_brief_user_message(
    *,
    topic_statement: str,
    facets: Sequence[TopicFacet],
    briefed_references: Sequence[BriefedReference],
) -> str:
    """Build the user message: topic, facets, and ordered briefed References."""
    parts: list[str] = [
        "Topic statement:",
        topic_statement.strip(),
        "",
        "Topic facets:",
    ]
    if not facets:
        parts.append("(none)")
    else:
        for facet in facets:
            parts.append(_format_facet(facet))
    parts.append("")
    parts.append(
        "Briefed References (newest pub_date first; null pub_date last). "
        "Use each citation_description as citations[].text when you cite that paper."
    )
    for index, item in enumerate(briefed_references, start=1):
        parts.append("")
        parts.append(f"### Briefed Reference {index}")
        parts.append(f"citation_description: {item.citation_description}")
        parts.append(f"doi: {item.doi.upper()}")
        parts.append(f"title: {item.title}")
        pub = item.pub_date.isoformat() if item.pub_date is not None else "(unknown)"
        parts.append(f"pub_date: {pub}")
        parts.append("paper_brief:")
        parts.append(json.dumps(item.paper_brief_content, ensure_ascii=False, indent=2))
    return "\n".join(parts)


def _format_facet(facet: TopicFacet) -> str:
    lines = [f"- {facet.label} (id={facet.id})"]
    if facet.intent:
        lines.append(f"  intent: {facet.intent}")
    if facet.concepts:
        lines.append(f"  concepts: {', '.join(facet.concepts)}")
    if facet.synonyms:
        lines.append(f"  synonyms: {', '.join(facet.synonyms)}")
    if facet.date_from or facet.date_to:
        lines.append(
            f"  dates: {facet.date_from or '…'} .. {facet.date_to or '…'}"
        )
    return "\n".join(lines)


def parse_topic_brief_content(raw: str) -> TopicBriefContent:
    """Validate LLM text as TopicBriefContent.

    Public OpenAI structured output is already JSON. Local gateways may wrap
    JSON in Markdown, add extra keys, or leak ANSI control bytes.
    """
    cleaned = _strip_ansi_and_controls(raw)
    payload = _extract_json_object(cleaned)
    payload = _repair_unescaped_controls_in_strings(payload)
    return TopicBriefContent.model_validate_json(payload)


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


def generate_topic_brief_content(
    *,
    topic_statement: str,
    facets: Sequence[TopicFacet],
    briefed_references: Sequence[BriefedReference],
) -> TopicBriefContent:
    """Call chat completions and parse TopicBriefContent. Tests must inject a stub."""
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
        system_prompt = f"{load_topic_brief_template()}\n\n{_GATEWAY_JSON_ONLY}"
    else:
        client = OpenAI(api_key=api_key)
        system_prompt = load_topic_brief_template()
    user_message = build_topic_brief_user_message(
        topic_statement=topic_statement,
        facets=facets,
        briefed_references=briefed_references,
    )
    create_kwargs: dict[str, object] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "response_format": type_to_response_format_param(TopicBriefContent),
    }
    if base_url is not None:
        create_kwargs["max_tokens"] = _GATEWAY_MAX_TOKENS
    completion = client.chat.completions.create(**create_kwargs)
    content = completion.choices[0].message.content
    if not content:
        raise ValueError("OpenAI returned no parsed topic brief")
    try:
        return parse_topic_brief_content(content)
    except (ValueError, ValidationError) as exc:
        dump = content[:_ASSISTANT_OUTPUT_MAX_CHARS]
        raise ValueError(
            f"{str(exc).rstrip()}\n\n{_ASSISTANT_OUTPUT_HEADING}\n{dump}"
        ) from exc
