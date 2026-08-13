"""Production submit wiring for fulfill_paper_metadata."""

from __future__ import annotations

from unittest.mock import patch

from paper_reviewer.flows.serve import FULFILL_DEPLOYMENT_REF
from paper_reviewer.flows.submit import submit_fulfill_paper_metadata


def test_submit_fulfill_calls_run_deployment_fire_and_forget() -> None:
    with patch("paper_reviewer.flows.submit.run_deployment") as mock_run:
        submit_fulfill_paper_metadata(42, "10.1000/EXAMPLE")

    mock_run.assert_called_once_with(
        name=FULFILL_DEPLOYMENT_REF,
        parameters={"paper_id": 42, "doi": "10.1000/EXAMPLE"},
        flow_run_name="10.1000/EXAMPLE",
        timeout=0,
    )


def test_fulfill_deployment_ref_matches_serve_name() -> None:
    assert FULFILL_DEPLOYMENT_REF == "fulfill_paper_metadata/default"
