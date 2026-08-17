"""Prefect flow wrappers for fulfill papers metadata."""

from __future__ import annotations

import inspect

from paper_reviewer.flows.inform_full_text import inform_full_text
from paper_reviewer.flows.inform_source_record import inform_source_record
from paper_reviewer.flows.ingest_paper import ingest_paper


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


def test_ingest_paper_flow_is_named_for_contract() -> None:
    assert ingest_paper.name == "ingest_paper"
    assert ingest_paper.flow_run_name == "{doi}"
    params = inspect.signature(ingest_paper).parameters
    assert list(params) == ["paper_id", "doi"]
