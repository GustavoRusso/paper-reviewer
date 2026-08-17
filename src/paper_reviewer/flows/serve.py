"""Serve Prefect deployments for local Compose (prefect-worker)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prefect.deployments.runner import RunnerDeployment

DEFAULT_DEPLOYMENT_NAME = "default"
CREATE_PAPER_BRIEF_DEPLOYMENT_REF = f"create_paper_brief/{DEFAULT_DEPLOYMENT_NAME}"
CREATE_TOPIC_BRIEF_DEPLOYMENT_REF = f"create_topic_brief/{DEFAULT_DEPLOYMENT_NAME}"
EVALUATE_PAPER_BRIEF_DEPLOYMENT_REF = f"evaluate_paper_brief/{DEFAULT_DEPLOYMENT_NAME}"
INGEST_PAPER_DEPLOYMENT_REF = f"ingest_paper/{DEFAULT_DEPLOYMENT_NAME}"
INGEST_PAPER_CONCURRENCY_LIMIT = 5


def served_deployments() -> Sequence[RunnerDeployment]:
    """Build the deployments that Compose ``prefect-worker`` serves."""
    from paper_reviewer.flows.create_paper_brief import create_paper_brief
    from paper_reviewer.flows.create_topic_brief import create_topic_brief
    from paper_reviewer.flows.evaluate_paper_brief import evaluate_paper_brief
    from paper_reviewer.flows.inform_full_text import inform_full_text
    from paper_reviewer.flows.inform_source_record import inform_source_record
    from paper_reviewer.flows.ingest_paper import ingest_paper

    return (
        inform_source_record.to_deployment(name=DEFAULT_DEPLOYMENT_NAME),
        inform_full_text.to_deployment(name=DEFAULT_DEPLOYMENT_NAME),
        create_paper_brief.to_deployment(name=DEFAULT_DEPLOYMENT_NAME),
        create_topic_brief.to_deployment(name=DEFAULT_DEPLOYMENT_NAME),
        evaluate_paper_brief.to_deployment(name=DEFAULT_DEPLOYMENT_NAME),
        ingest_paper.to_deployment(
            name=DEFAULT_DEPLOYMENT_NAME,
            concurrency_limit=INGEST_PAPER_CONCURRENCY_LIMIT,
        ),
    )


if __name__ == "__main__":
    from prefect import serve

    serve(*served_deployments())
