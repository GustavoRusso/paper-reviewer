"""Prefect submit helpers for fulfill papers metadata."""

from __future__ import annotations

from prefect.deployments import run_deployment

from paper_reviewer.flows.serve import INFORM_DEPLOYMENT_REF


def submit_inform_paper_from_source(paper_id: int, doi: str) -> None:
    """Enqueue ``inform_paper_from_source`` on the served Prefect deployment.

    Fire-and-forget (``timeout=0``): progress is read from durable ``Paper``
    columns, not from the Prefect run handle. Run name is the paper DOI for
    console searchability.
    """
    run_deployment(
        name=INFORM_DEPLOYMENT_REF,
        parameters={"paper_id": paper_id, "doi": doi},
        flow_run_name=doi,
        timeout=0,
    )
