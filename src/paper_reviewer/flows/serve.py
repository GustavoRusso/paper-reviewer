"""Serve Prefect deployments for local Compose (prefect-worker)."""

from __future__ import annotations

from paper_reviewer.flows.inform_paper_from_source import inform_paper_from_source

INFORM_DEPLOYMENT_NAME = "default"
INFORM_DEPLOYMENT_REF = f"inform_paper_from_source/{INFORM_DEPLOYMENT_NAME}"


if __name__ == "__main__":
    inform_paper_from_source.serve(name=INFORM_DEPLOYMENT_NAME)
