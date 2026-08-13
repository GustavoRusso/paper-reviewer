"""Prompt builder for create_paper_brief: template file plus full text."""

from __future__ import annotations

from paper_reviewer.topic_brief_generation.generate_paper_brief.llm import (
    build_brief_user_message,
    load_paper_brief_template,
)


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
