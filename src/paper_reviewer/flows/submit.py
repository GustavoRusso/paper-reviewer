"""Prefect submit helpers for fulfill papers metadata."""

from __future__ import annotations

import time

from prefect.deployments import run_deployment

from paper_reviewer.flows.serve import INFORM_DEPLOYMENT_REF

_SUBMIT_MAX_ATTEMPTS = 3
_SUBMIT_RETRY_DELAY_SECONDS = 0.5


def submit_inform_paper_from_source(paper_id: int, doi: str) -> None:
    """Enqueue ``inform_paper_from_source`` on the served Prefect deployment.

    Fire-and-forget (``timeout=0``): progress is read from durable ``Paper``
    columns, not from the Prefect run handle. Run name is the paper DOI for
    console searchability.
    """
    last_exc: Exception | None = None
    for attempt in range(1, _SUBMIT_MAX_ATTEMPTS + 1):
        try:
            run_deployment(
                name=INFORM_DEPLOYMENT_REF,
                parameters={"paper_id": paper_id, "doi": doi},
                flow_run_name=doi,
                timeout=0,
            )
            return
        except Exception as exc:
            last_exc = exc
            if attempt < _SUBMIT_MAX_ATTEMPTS:
                time.sleep(_SUBMIT_RETRY_DELAY_SECONDS)
    assert last_exc is not None
    raise last_exc
