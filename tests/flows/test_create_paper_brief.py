"""Prefect flow wrappers for generate paper brief."""

from __future__ import annotations

import inspect

from paper_reviewer.flows.create_paper_brief import create_paper_brief
from paper_reviewer.flows.serve import CREATE_PAPER_BRIEF_DEPLOYMENT_REF


def test_create_paper_brief_flow_is_named_for_contract() -> None:
    assert create_paper_brief.name == "create_paper_brief"
    assert create_paper_brief.flow_run_name == "{doi}"
    params = inspect.signature(create_paper_brief).parameters
    assert list(params) == ["paper_id", "doi", "force"]
    assert params["force"].default is False


def test_create_paper_brief_deployment_ref() -> None:
    assert CREATE_PAPER_BRIEF_DEPLOYMENT_REF == "create_paper_brief/default"
