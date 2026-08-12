"""Production submit wiring for inform_paper_from_source."""

from __future__ import annotations

from unittest.mock import patch

from paper_reviewer.flows.serve import INFORM_DEPLOYMENT_REF
from paper_reviewer.flows.submit import submit_inform_paper_from_source


def test_submit_inform_calls_run_deployment_fire_and_forget() -> None:
    with patch("paper_reviewer.flows.submit.run_deployment") as mock_run:
        submit_inform_paper_from_source(42, "10.1000/EXAMPLE")

    mock_run.assert_called_once_with(
        name=INFORM_DEPLOYMENT_REF,
        parameters={"paper_id": 42, "doi": "10.1000/EXAMPLE"},
        flow_run_name="10.1000/EXAMPLE",
        timeout=0,
    )


def test_inform_deployment_ref_matches_serve_name() -> None:
    assert INFORM_DEPLOYMENT_REF == "inform_paper_from_source/default"
