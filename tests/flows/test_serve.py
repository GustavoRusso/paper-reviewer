"""Served Prefect deployments: ingest_paper concurrency cap."""

from __future__ import annotations

from paper_reviewer.flows.serve import (
    INGEST_PAPER_CONCURRENCY_LIMIT,
    served_deployments,
)

_OTHER_FLOW_NAMES = (
    "fulfill_paper_metadata",
    "inform_source_record",
    "inform_full_text",
    "create_paper_brief",
    "create_topic_brief",
    "evaluate_paper_brief",
)


def _by_flow_name() -> dict[str, object]:
    return {deployment.flow_name: deployment for deployment in served_deployments()}


def test_ingest_paper_concurrency_limit_is_five() -> None:
    assert INGEST_PAPER_CONCURRENCY_LIMIT == 5
    ingest = _by_flow_name()["ingest_paper"]
    assert ingest.concurrency_limit == INGEST_PAPER_CONCURRENCY_LIMIT


def test_other_served_deployments_have_no_concurrency_cap() -> None:
    by_flow = _by_flow_name()
    for flow_name in _OTHER_FLOW_NAMES:
        assert by_flow[flow_name].concurrency_limit is None
