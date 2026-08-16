"""Production submit wiring for fulfill_paper_metadata."""

from __future__ import annotations

from unittest.mock import patch

from paper_reviewer.flows.serve import (
    CREATE_PAPER_BRIEF_DEPLOYMENT_REF,
    CREATE_TOPIC_BRIEF_DEPLOYMENT_REF,
    FULFILL_DEPLOYMENT_REF,
    REGENERATE_PAPER_DEPLOYMENT_REF,
)
from paper_reviewer.flows.submit import (
    submit_create_paper_brief,
    submit_create_topic_brief,
    submit_fulfill_paper_metadata,
    submit_regenerate_paper,
)


def test_submit_fulfill_calls_run_deployment_fire_and_forget() -> None:
    with patch("paper_reviewer.flows.submit.run_deployment") as mock_run:
        submit_fulfill_paper_metadata(42, "10.1000/EXAMPLE")

    mock_run.assert_called_once_with(
        name=FULFILL_DEPLOYMENT_REF,
        parameters={"paper_id": 42, "doi": "10.1000/EXAMPLE"},
        flow_run_name="10.1000/EXAMPLE",
        timeout=0,
    )


def test_submit_create_paper_brief_does_not_pass_force() -> None:
    with patch("paper_reviewer.flows.submit.run_deployment") as mock_run:
        submit_create_paper_brief(42, "10.1000/EXAMPLE")

    mock_run.assert_called_once_with(
        name=CREATE_PAPER_BRIEF_DEPLOYMENT_REF,
        parameters={"paper_id": 42, "doi": "10.1000/EXAMPLE"},
        flow_run_name="10.1000/EXAMPLE",
        timeout=0,
    )


def test_submit_create_topic_brief_passes_force_true() -> None:
    with patch("paper_reviewer.flows.submit.run_deployment") as mock_run:
        submit_create_topic_brief(7)

    mock_run.assert_called_once_with(
        name=CREATE_TOPIC_BRIEF_DEPLOYMENT_REF,
        parameters={"topic_scope_id": 7, "force": True},
        flow_run_name="topic-scope-7",
        timeout=0,
    )


def test_fulfill_deployment_ref_matches_serve_name() -> None:
    assert FULFILL_DEPLOYMENT_REF == "fulfill_paper_metadata/default"


def test_create_paper_brief_deployment_ref_matches_serve_name() -> None:
    assert CREATE_PAPER_BRIEF_DEPLOYMENT_REF == "create_paper_brief/default"


def test_create_topic_brief_deployment_ref_matches_serve_name() -> None:
    assert CREATE_TOPIC_BRIEF_DEPLOYMENT_REF == "create_topic_brief/default"


def test_submit_regenerate_paper_calls_run_deployment_fire_and_forget() -> None:
    with patch("paper_reviewer.flows.submit.run_deployment") as mock_run:
        submit_regenerate_paper(42, "10.1000/EXAMPLE")

    mock_run.assert_called_once_with(
        name=REGENERATE_PAPER_DEPLOYMENT_REF,
        parameters={"paper_id": 42, "doi": "10.1000/EXAMPLE"},
        flow_run_name="10.1000/EXAMPLE",
        timeout=0,
    )
    called_name = mock_run.call_args.kwargs["name"]
    assert called_name == "regenerate_paper/default"
    assert "inform_source_record" not in called_name
    assert "inform_full_text" not in called_name
    assert "create_paper_brief" not in called_name
    assert "create_topic_brief" not in called_name
    assert "fulfill_paper_metadata" not in called_name


def test_regenerate_paper_deployment_ref_matches_serve_name() -> None:
    assert REGENERATE_PAPER_DEPLOYMENT_REF == "regenerate_paper/default"
