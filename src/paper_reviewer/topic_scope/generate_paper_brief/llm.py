"""Load the paper-brief template and call the production LLM."""

from __future__ import annotations

import logging
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from pydantic import ValidationError

from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    PaperBriefContent,
    PaperBriefLlmResult,
)

_TEMPLATE_PATH = Path(__file__).parent / "paper_brief_template.md"
_DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1"}
_PLACEHOLDER_API_KEY = "not-needed"
_GATEWAY_MAX_TOKENS = 4096
_GATEWAY_FULL_TEXT_MAX_CHARS = 8000
_GATEWAY_JSON_ONLY = (
    "Reply with a single JSON object only. "
    "The first non-whitespace character must be `{`."
)
_GATEWAY_TRUNCATE_NOTE = "\n\n[truncated for local gateway context]"
_ASSISTANT_OUTPUT_HEADING = "Assistant output:"
_ASSISTANT_OUTPUT_MAX_CHARS = 8000
_ANSI_RE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\)|.)")
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL | re.IGNORECASE)
_MAJOR_HEADING_RE = re.compile(
    r"^(?:(?P<num>\d+)\s+)?(?P<title>[A-Za-z][A-Za-z &/\-]{1,70}):?\s*$"
)
_KEEP_HIGH = frozenset(
    {
        "abstract",
        "author summary",
        "methods",
        "materials and methods",
        "materials",
        "methodology",
        "results",
        "results and conclusions",
        "results and discussion",
    }
)
_KEEP_LOW = frozenset(
    {
        "introduction",
        "background",
        "discussion",
        "conclusion",
        "conclusions",
        "limitations",
        "recommendations",
    }
)
_DROP_HEADINGS = frozenset(
    {
        "abbreviations",
        "acknowledgement",
        "acknowledgements",
        "acknowledgment",
        "acknowledgments",
        "appendix",
        "appendices",
        "article information",
        "author contributions",
        "author information",
        "authors contributions",
        "availability of data and materials",
        "bibliography",
        "citation",
        "competing interests",
        "conflict of interest",
        "conflicts of interest",
        "consent for publication",
        "copyright",
        "corresponding author",
        "data and materials availability",
        "data availability",
        "data availability statement",
        "disclosure",
        "ethical approval",
        "ethics",
        "ethics statement",
        "funding",
        "informed consent",
        "journal information",
        "keywords",
        "license",
        "literature cited",
        "open access",
        "references",
        "supplementary",
        "supplementary information",
        "supplementary materials",
        "supporting information",
    }
)


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


def template_field_contract() -> list[tuple[str, bool]]:
    """Return (id, required) pairs from the template YAML front matter, in order."""
    template = load_paper_brief_template()
    if not template.startswith("---"):
        raise ValueError("paper_brief_template.md is missing YAML front matter")
    end = template.find("\n---", 3)
    if end < 0:
        raise ValueError("paper_brief_template.md front matter is not closed")
    fields: list[tuple[str, bool]] = []
    current_id: str | None = None
    for line in template[3:end].splitlines():
        stripped = line.strip()
        if stripped.startswith("- id:"):
            current_id = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("required:") and current_id is not None:
            required = stripped.split(":", 1)[1].strip() == "true"
            fields.append((current_id, required))
            current_id = None
    return fields


def template_field_ids() -> list[str]:
    """Return JSON field ids from the template YAML front matter, in order."""
    return [field_id for field_id, _required in template_field_contract()]


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


def extract_scientific_full_text(full_text_plain: str) -> str:
    """Keep scientific sections; drop boilerplate and references.

    Used for every LLM path. If the article has no section headings, return
    the original text.
    """
    sections = _extract_keep_sections(full_text_plain)
    if sections is None:
        return full_text_plain
    return _render_sections(sections)


def clip_full_text_for_gateway(
    full_text_plain: str,
    *,
    max_chars: int = _GATEWAY_FULL_TEXT_MAX_CHARS,
) -> str:
    """Extract scientific sections, then fit a small local context window."""
    sections = _extract_keep_sections(full_text_plain)
    if sections is None:
        return _prefix_clip(full_text_plain, max_chars)
    return _fit_keep_sections(sections, max_chars)


def _prefix_clip(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    keep = max_chars - len(_GATEWAY_TRUNCATE_NOTE)
    if keep < 1:
        return _GATEWAY_TRUNCATE_NOTE.strip()
    return text[:keep] + _GATEWAY_TRUNCATE_NOTE


def _normalize_major_heading(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or re.match(r"^\d+\.\d+", stripped):
        return None
    matched = _MAJOR_HEADING_RE.match(stripped)
    if matched is None:
        return None
    title = re.sub(r"\s+", " ", matched.group("title")).strip().lower()
    title = title.replace("&", "and")
    if title in _KEEP_HIGH or title in _KEEP_LOW or title in _DROP_HEADINGS:
        return title
    return None


def _extract_keep_sections(full_text_plain: str) -> list[tuple[str, str, str]] | None:
    lines = full_text_plain.splitlines()
    blocks: list[tuple[str, list[str]]] = [("", [])]
    found_heading = False
    for line in lines:
        heading = _normalize_major_heading(line)
        if heading is None:
            blocks[-1][1].append(line)
            continue
        found_heading = True
        blocks.append((line.strip(), []))
    if not found_heading:
        return None
    keep: list[tuple[str, str, str]] = []
    for raw_heading, body_lines in blocks:
        key = _normalize_major_heading(raw_heading) if raw_heading else None
        if key is None or key in _DROP_HEADINGS:
            continue
        body = "\n".join(body_lines).strip()
        if not body:
            continue
        priority = "high" if key in _KEEP_HIGH else "low"
        keep.append((raw_heading, body, priority))
    if not keep:
        return None
    return keep


def _render_sections(sections: list[tuple[str, str, str]]) -> str:
    parts: list[str] = []
    for heading, body, _priority in sections:
        if not body.strip():
            continue
        parts.append(f"{heading}\n\n{body.strip()}")
    return "\n\n".join(parts)


def _fit_keep_sections(sections: list[tuple[str, str, str]], max_chars: int) -> str:
    rendered = _render_sections(sections)
    if len(rendered) <= max_chars:
        return rendered
    working = [(heading, body, priority) for heading, body, priority in sections]
    extra = len(_render_sections(working)) - max_chars + len(_GATEWAY_TRUNCATE_NOTE)
    for index in range(len(working) - 1, -1, -1):
        if extra <= 0:
            break
        heading, body, priority = working[index]
        if priority != "low":
            continue
        if len(body) <= extra:
            extra -= len(body)
            working[index] = (heading, "", priority)
            continue
        working[index] = (heading, body[: len(body) - extra].rstrip(), priority)
        extra = 0
    fitted = _render_sections(working)
    if len(fitted) <= max_chars - len(_GATEWAY_TRUNCATE_NOTE):
        return fitted + _GATEWAY_TRUNCATE_NOTE
    high_only = [item for item in working if item[2] == "high" and item[1].strip()]
    high_text = _render_sections(high_only)
    if high_text:
        return _prefix_clip(high_text, max_chars)
    return _prefix_clip(rendered, max_chars)


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


def _to_jsonable_openai_part(value: object) -> object:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    if isinstance(value, (list, tuple)):
        return [_to_jsonable_openai_part(item) for item in value]
    if hasattr(value, "__dict__"):
        return {
            key: _to_jsonable_openai_part(raw)
            for key, raw in vars(value).items()
            if not key.startswith("_")
        }
    return value


def _serialize_openai_part(value: object) -> str:
    return json.dumps(_to_jsonable_openai_part(value), ensure_ascii=True, indent=2)


def _format_usage_log(usage: object | None) -> str:
    if usage is None:
        return "OpenAI usage: absent"
    usage_json = _to_jsonable_openai_part(usage)
    assert isinstance(usage_json, dict)
    labeled_lines: list[str] = []
    for key, value in usage_json.items():
        if isinstance(value, (dict, list)):
            labeled_lines.append(f"{key}:\n{_serialize_openai_part(value)}")
        else:
            labeled_lines.append(f"{key}: {value}")
    labeled = "\n".join(labeled_lines)
    return (
        "OpenAI usage:\n"
        f"{labeled}\n\n"
        "OpenAI usage (raw JSON):\n"
        f"{_serialize_openai_part(usage_json)}"
    )


def _emit_openai_log(message: str) -> None:
    try:
        from prefect import get_run_logger

        get_run_logger().info(message)
    except Exception:
        logging.getLogger(__name__).info(message)


def _usage_int(usage_json: dict[str, object], key: str) -> int | None:
    value = usage_json.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def usage_integers(
    usage: object | None,
) -> tuple[int | None, int | None, int | None]:
    if usage is None:
        return None, None, None
    usage_json = _to_jsonable_openai_part(usage)
    if not isinstance(usage_json, dict):
        return None, None, None
    return (
        _usage_int(usage_json, "prompt_tokens"),
        _usage_int(usage_json, "completion_tokens"),
        _usage_int(usage_json, "total_tokens"),
    )


def generate_paper_brief_content(
    full_text_plain: str,
    *,
    title: str,
    journal: str | None,
    published_year: int | None,
) -> PaperBriefLlmResult:
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
        system_prompt = f"{load_paper_brief_template()}\n\n{_GATEWAY_JSON_ONLY}"
        article_text = clip_full_text_for_gateway(full_text_plain)
    else:
        client = OpenAI(api_key=api_key)
        system_prompt = load_paper_brief_template()
        article_text = extract_scientific_full_text(full_text_plain)
    create_kwargs: dict[str, object] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": build_brief_user_message(
                    full_text_plain=article_text,
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
    _emit_openai_log(f"OpenAI request:\n{_serialize_openai_part(create_kwargs)}")
    completion = client.chat.completions.create(**create_kwargs)
    _emit_openai_log(
        "OpenAI response message:\n"
        f"{_serialize_openai_part(completion.choices[0].message)}"
    )
    usage = getattr(completion, "usage", None)
    _emit_openai_log(_format_usage_log(usage))
    content = completion.choices[0].message.content
    if not content:
        raise ValueError("OpenAI returned no parsed paper brief")
    try:
        parsed = parse_paper_brief_content(content)
    except (ValueError, ValidationError) as exc:
        dump = content[:_ASSISTANT_OUTPUT_MAX_CHARS]
        raise ValueError(
            f"{str(exc).rstrip()}\n\n{_ASSISTANT_OUTPUT_HEADING}\n{dump}"
        ) from exc
    prompt_tokens, completion_tokens, total_tokens = usage_integers(usage)
    return PaperBriefLlmResult(
        content=parsed,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )
