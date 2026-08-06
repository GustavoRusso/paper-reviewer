"""Query intake: accept a free-form research query."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from paper_reviewer.schemas.query_intake import ResearchQuery, accept_query_intake


def test_accept_query_intake_returns_research_query() -> None:
    result = accept_query_intake("GLP-1 agonists in heart failure")

    assert isinstance(result, ResearchQuery)
    assert result.text == "GLP-1 agonists in heart failure"


def test_accept_query_intake_strips_whitespace() -> None:
    result = accept_query_intake("  mitochondrial dysfunction  \n")

    assert result.text == "mitochondrial dysfunction"


def test_accept_query_intake_rejects_empty_string() -> None:
    with pytest.raises(ValidationError):
        accept_query_intake("")


def test_accept_query_intake_rejects_whitespace_only() -> None:
    with pytest.raises(ValidationError):
        accept_query_intake("   \n\t  ")
