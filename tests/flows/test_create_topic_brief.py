"""Prefect flow wrappers for topic brief generation."""

from __future__ import annotations

import inspect

from paper_reviewer.flows.create_topic_brief import create_topic_brief
from paper_reviewer.flows.serve import CREATE_TOPIC_BRIEF_DEPLOYMENT_REF


def test_create_topic_brief_flow_is_named_for_contract() -> None:
    assert create_topic_brief.name == "create_topic_brief"
    params = inspect.signature(create_topic_brief).parameters
    assert list(params) == ["topic_scope_id", "force"]
    assert params["force"].default is True


def test_create_topic_brief_deployment_ref() -> None:
    assert CREATE_TOPIC_BRIEF_DEPLOYMENT_REF == "create_topic_brief/default"
