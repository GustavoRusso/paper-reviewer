"""Prefect flow wrappers for fulfill papers metadata."""

from __future__ import annotations

import inspect

from paper_reviewer.flows.fulfill_paper_metadata import fulfill_paper_metadata
from paper_reviewer.flows.inform_full_text import inform_full_text
from paper_reviewer.flows.inform_source_record import inform_source_record
from paper_reviewer.flows.regenerate_paper import regenerate_paper


def test_inform_source_record_flow_is_named_for_contract() -> None:
    assert inform_source_record.name == "inform_source_record"
    assert inform_source_record.flow_run_name == "{doi}"
    params = inspect.signature(inform_source_record).parameters
    assert list(params) == ["paper_id", "doi", "force"]
    assert params["force"].default is False


def test_inform_full_text_flow_is_named_for_contract() -> None:
    assert inform_full_text.name == "inform_full_text"
    assert inform_full_text.flow_run_name == "{doi}"
    params = inspect.signature(inform_full_text).parameters
    assert list(params) == ["paper_id", "doi", "force"]
    assert params["force"].default is False


def test_fulfill_paper_metadata_flow_is_named_for_contract() -> None:
    assert fulfill_paper_metadata.name == "fulfill_paper_metadata"
    assert fulfill_paper_metadata.flow_run_name == "{doi}"
    params = inspect.signature(fulfill_paper_metadata).parameters
    assert list(params) == ["paper_id", "doi"]


def test_regenerate_paper_flow_is_named_for_contract() -> None:
    assert regenerate_paper.name == "regenerate_paper"
    assert regenerate_paper.flow_run_name == "{doi}"
    params = inspect.signature(regenerate_paper).parameters
    assert list(params) == ["paper_id", "doi"]
