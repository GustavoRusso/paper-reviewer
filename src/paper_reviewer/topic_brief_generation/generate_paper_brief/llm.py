"""Load the paper-brief template and call the production LLM."""

from __future__ import annotations

import os
from pathlib import Path

from paper_reviewer.schemas.topic_brief_generation.generate_paper_brief import (
    PaperBriefContent,
)

_TEMPLATE_PATH = Path(__file__).parent / "paper_brief_template.md"
_OPENAI_MODEL = "gpt-4o-mini"


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


def generate_paper_brief_content(
    full_text_plain: str,
    *,
    title: str,
    journal: str | None,
    published_year: int | None,
) -> PaperBriefContent:
    """Call OpenAI structured parse. Tests must inject a stub instead."""
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY") or None
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")
    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.parse(
        model=_OPENAI_MODEL,
        messages=[
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
        response_format=PaperBriefContent,
    )
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("OpenAI returned no parsed paper brief")
    return parsed
