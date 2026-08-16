"""Topic intake: accept a free-form topic statement."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from paper_reviewer.schemas.topic_scope.topic_intake import (
    TopicStatement,
    accept_topic_intake,
)


def test_accept_topic_intake_returns_topic_statement() -> None:
    result = accept_topic_intake("GLP-1 agonists in heart failure")

    assert isinstance(result, TopicStatement)
    assert result.text == "GLP-1 agonists in heart failure"


def test_accept_topic_intake_strips_whitespace() -> None:
    result = accept_topic_intake("  mitochondrial dysfunction  \n")

    assert result.text == "mitochondrial dysfunction"


def test_accept_topic_intake_rejects_empty_string() -> None:
    with pytest.raises(ValidationError):
        accept_topic_intake("")


def test_accept_topic_intake_rejects_whitespace_only() -> None:
    with pytest.raises(ValidationError):
        accept_topic_intake("   \n\t  ")
