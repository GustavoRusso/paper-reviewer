"""Serve Prefect deployments for local Compose (prefect-worker)."""

from __future__ import annotations

FULFILL_DEPLOYMENT_NAME = "default"
FULFILL_DEPLOYMENT_REF = f"fulfill_paper_metadata/{FULFILL_DEPLOYMENT_NAME}"
CREATE_PAPER_BRIEF_DEPLOYMENT_REF = f"create_paper_brief/{FULFILL_DEPLOYMENT_NAME}"


if __name__ == "__main__":
    from prefect import serve

    from paper_reviewer.flows.create_paper_brief import create_paper_brief
    from paper_reviewer.flows.fulfill_paper_metadata import fulfill_paper_metadata
    from paper_reviewer.flows.inform_full_text import inform_full_text
    from paper_reviewer.flows.inform_source_record import inform_source_record

    serve(
        fulfill_paper_metadata.to_deployment(name=FULFILL_DEPLOYMENT_NAME),
        inform_source_record.to_deployment(name=FULFILL_DEPLOYMENT_NAME),
        inform_full_text.to_deployment(name=FULFILL_DEPLOYMENT_NAME),
        create_paper_brief.to_deployment(name=FULFILL_DEPLOYMENT_NAME),
    )
