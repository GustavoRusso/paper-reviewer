"""Query intake: free-form research query validation."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ResearchQuery(BaseModel):
    """Validated research query from Query intake."""

    text: str = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def strip_and_require_non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("research query must not be empty")
        return stripped


def accept_query_intake(raw_text: str) -> ResearchQuery:
    """Accept raw Query intake text as a validated ResearchQuery."""
    return ResearchQuery(text=raw_text)
