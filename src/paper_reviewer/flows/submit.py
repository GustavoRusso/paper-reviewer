"""Prefect submit helpers for fulfill papers metadata and briefs."""

from __future__ import annotations

import time

from prefect.deployments import run_deployment

from paper_reviewer.flows.serve import (
    CREATE_PAPER_BRIEF_DEPLOYMENT_REF,
    CREATE_TOPIC_BRIEF_DEPLOYMENT_REF,
    FULFILL_DEPLOYMENT_REF,
    INGEST_PAPER_DEPLOYMENT_REF,
)

_SUBMIT_MAX_ATTEMPTS = 3
_SUBMIT_RETRY_DELAY_SECONDS = 0.5


def _run_paper_deployment(name: str, paper_id: int, doi: str) -> None:
    last_exc: Exception | None = None
    for attempt in range(1, _SUBMIT_MAX_ATTEMPTS + 1):
        try:
            run_deployment(
                name=name,
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


def submit_fulfill_paper_metadata(paper_id: int, doi: str) -> None:
    """Enqueue ``fulfill_paper_metadata`` on the served Prefect deployment.

    Fire-and-forget (``timeout=0``): progress is read from durable ``Paper``
    columns, not from the Prefect run handle. Run name is the paper DOI for
    console searchability.
    """
    _run_paper_deployment(FULFILL_DEPLOYMENT_REF, paper_id, doi)


def submit_create_paper_brief(paper_id: int, doi: str) -> None:
    """Enqueue ``create_paper_brief`` on the served Prefect deployment.

    Does not pass ``force``. Progress is read from durable ``PaperBrief``
    columns, not from the Prefect run handle.
    """
    _run_paper_deployment(CREATE_PAPER_BRIEF_DEPLOYMENT_REF, paper_id, doi)


def submit_ingest_paper(paper_id: int, doi: str) -> None:
    """Enqueue ``ingest_paper`` on the served Prefect deployment.

    The orchestrator always forces. Progress is read from durable ``Paper``
    and ``PaperBrief`` columns, not from the Prefect run handle.
    """
    _run_paper_deployment(INGEST_PAPER_DEPLOYMENT_REF, paper_id, doi)


def submit_create_topic_brief(topic_scope_id: int) -> None:
    """Enqueue ``create_topic_brief`` on the served Prefect deployment.

    Always passes ``force=True`` (overwrite-on-click). Progress is read from
    durable ``TopicBrief`` columns, not from the Prefect run handle.
    """
    last_exc: Exception | None = None
    for attempt in range(1, _SUBMIT_MAX_ATTEMPTS + 1):
        try:
            run_deployment(
                name=CREATE_TOPIC_BRIEF_DEPLOYMENT_REF,
                parameters={"topic_scope_id": topic_scope_id, "force": True},
                flow_run_name=f"topic-scope-{topic_scope_id}",
                timeout=0,
            )
            return
        except Exception as exc:
            last_exc = exc
            if attempt < _SUBMIT_MAX_ATTEMPTS:
                time.sleep(_SUBMIT_RETRY_DELAY_SECONDS)
    assert last_exc is not None
    raise last_exc
