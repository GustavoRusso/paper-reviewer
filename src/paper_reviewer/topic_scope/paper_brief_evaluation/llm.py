"""Load the evaluation template and call the production judge LLM."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import ValidationError

from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    PaperBriefContent,
)
from paper_reviewer.schemas.topic_scope.paper_brief_evaluation import (
    PaperBriefEvaluation,
)
from paper_reviewer.topic_scope.generate_paper_brief.llm import (
    _ASSISTANT_OUTPUT_HEADING,
    _ASSISTANT_OUTPUT_MAX_CHARS,
    _DEFAULT_OPENAI_MODEL,
    _GATEWAY_JSON_ONLY,
    _GATEWAY_REASONING_EFFORT,
    _PLACEHOLDER_API_KEY,
    _call_and_log,
    _extract_json_object,
    _repair_unescaped_controls_in_strings,
    _strip_ansi_and_controls,
    assistant_message_text,
    build_openai_client,
    clip_full_text_for_gateway,
    extract_scientific_full_text,
    resolve_openai_base_url,
    resolve_openai_model,
    template_field_contract,
)

_TEMPLATE_PATH = Path(__file__).parent / "paper_brief_evaluation_template.md"
_JUDGE_MAX_TOKENS = 8192


def apply_judge_chat_options(
    create_kwargs: dict[str, object],
    *,
    gateway: bool,
) -> None:
    """Set judge completion limits for any chat backend."""
    create_kwargs["max_tokens"] = _JUDGE_MAX_TOKENS
    if gateway:
        create_kwargs["reasoning_effort"] = _GATEWAY_REASONING_EFFORT


def load_paper_brief_evaluation_template() -> str:
    """Return the shared Markdown template (system prompt)."""
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


def evaluation_criterion_ids() -> list[str]:
    """Return G-Eval criterion ids from the template YAML front matter, in order."""
    template = load_paper_brief_evaluation_template()
    if not template.startswith("---"):
        raise ValueError(
            "paper_brief_evaluation_template.md is missing YAML front matter"
        )
    end = template.find("\n---", 3)
    if end < 0:
        raise ValueError(
            "paper_brief_evaluation_template.md front matter is not closed"
        )
    ids: list[str] = []
    for line in template[3:end].splitlines():
        stripped = line.strip()
        if stripped.startswith("- id:"):
            ids.append(stripped.split(":", 1)[1].strip())
    return ids


def build_evaluation_user_message(
    *,
    full_text_plain: str,
    content: PaperBriefContent,
) -> str:
    """Build the user message: field contract, brief JSON, and full text."""
    contract_lines: list[str] = []
    for field_id, required in template_field_contract():
        flag = "required" if required else "optional"
        contract_lines.append(f"- {field_id}: {flag}")
    contract = "\n".join(contract_lines)
    brief_json = content.model_dump_json(indent=2)
    return (
        "Generator field contract (ids and required flags):\n"
        f"{contract}\n\n"
        "Paper brief JSON:\n"
        f"{brief_json}\n\n"
        "Article full text:\n"
        f"{full_text_plain}"
    )


def parse_paper_brief_evaluation(raw: str) -> PaperBriefEvaluation:
    """Validate LLM text as PaperBriefEvaluation."""
    cleaned = _strip_ansi_and_controls(raw)
    payload = _extract_json_object(cleaned)
    payload = _repair_unescaped_controls_in_strings(payload)
    return PaperBriefEvaluation.model_validate_json(payload)


def judge_paper_brief_evaluation(
    full_text_plain: str,
    *,
    content: PaperBriefContent,
) -> PaperBriefEvaluation:
    """Call chat completions and parse PaperBriefEvaluation. Tests must inject a stub."""
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
    client = build_openai_client(api_key=api_key, base_url=base_url)
    if base_url is not None:
        system_prompt = (
            f"{load_paper_brief_evaluation_template()}\n\n{_GATEWAY_JSON_ONLY}"
        )
        article_text = clip_full_text_for_gateway(full_text_plain)
    else:
        system_prompt = load_paper_brief_evaluation_template()
        article_text = extract_scientific_full_text(full_text_plain)
    create_kwargs: dict[str, object] = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": build_evaluation_user_message(
                    full_text_plain=article_text,
                    content=content,
                ),
            },
        ],
        "response_format": type_to_response_format_param(PaperBriefEvaluation),
    }
    apply_judge_chat_options(create_kwargs, gateway=base_url is not None)
    completion = _call_and_log(client, create_kwargs)
    raw_content = assistant_message_text(completion.choices[0].message)  # type: ignore[union-attr]
    if not raw_content:
        raise ValueError("OpenAI returned no parsed paper brief evaluation")
    try:
        return parse_paper_brief_evaluation(raw_content)
    except (ValueError, ValidationError) as exc:
        dump = raw_content[:_ASSISTANT_OUTPUT_MAX_CHARS]
        raise ValueError(
            f"{str(exc).rstrip()}\n\n{_ASSISTANT_OUTPUT_HEADING}\n{dump}"
        ) from exc
