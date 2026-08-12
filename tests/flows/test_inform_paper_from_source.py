"""Prefect flow wrapper for inform_paper_from_source."""

from __future__ import annotations

import inspect

from paper_reviewer.flows.inform_paper_from_source import inform_paper_from_source


def test_inform_flow_is_named_for_contract() -> None:
    assert inform_paper_from_source.name == "inform_paper_from_source"


def test_inform_flow_accepts_paper_id_and_doi_parameters() -> None:
    params = inspect.signature(inform_paper_from_source).parameters
    assert list(params) == ["paper_id", "doi"]
