"""Topic intake: free-form topic statement validation."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class TopicStatement(BaseModel):
    """Validated topic statement from Topic intake."""

    text: str = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def strip_and_require_non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("topic statement must not be empty")
        return stripped


def accept_topic_intake(raw_text: str) -> TopicStatement:
    """Accept raw Topic intake text as a validated TopicStatement."""
    return TopicStatement(text=raw_text)
