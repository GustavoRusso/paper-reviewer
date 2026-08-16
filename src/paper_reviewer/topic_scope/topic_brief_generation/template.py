"""Load the topic-brief template front matter helpers."""

from __future__ import annotations

from pathlib import Path

_TEMPLATE_PATH = Path(__file__).parent / "topic_brief_template.md"


def load_topic_brief_template() -> str:
    """Return the shared Markdown template (system prompt)."""
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


def template_field_ids() -> list[str]:
    """Return JSON field ids from the template YAML front matter, in order."""
    template = load_topic_brief_template()
    if not template.startswith("---"):
        raise ValueError("topic_brief_template.md is missing YAML front matter")
    end = template.find("\n---", 3)
    if end < 0:
        raise ValueError("topic_brief_template.md front matter is not closed")
    ids: list[str] = []
    for line in template[3:end].splitlines():
        stripped = line.strip()
        if stripped.startswith("- id:"):
            ids.append(stripped.split(":", 1)[1].strip())
    return ids
