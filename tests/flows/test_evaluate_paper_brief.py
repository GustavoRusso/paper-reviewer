"""Prefect flow wrappers for paper brief evaluation."""

from __future__ import annotations

import inspect

from paper_reviewer.flows.evaluate_paper_brief import evaluate_paper_brief
from paper_reviewer.flows.serve import EVALUATE_PAPER_BRIEF_DEPLOYMENT_REF


def test_evaluate_paper_brief_flow_is_named_for_contract() -> None:
    assert evaluate_paper_brief.name == "evaluate_paper_brief"
    assert evaluate_paper_brief.flow_run_name == "{doi}"
    params = inspect.signature(evaluate_paper_brief).parameters
    assert list(params) == ["paper_id", "doi", "force"]
    assert params["force"].default is False


def test_evaluate_paper_brief_deployment_ref() -> None:
    assert EVALUATE_PAPER_BRIEF_DEPLOYMENT_REF == "evaluate_paper_brief/default"
