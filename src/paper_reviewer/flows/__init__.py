"""Prefect flows for paper-reviewer jobs."""

from paper_reviewer.flows.create_paper_brief import create_paper_brief
from paper_reviewer.flows.evaluate_paper_brief import evaluate_paper_brief
from paper_reviewer.flows.inform_full_text import inform_full_text
from paper_reviewer.flows.inform_source_record import inform_source_record
from paper_reviewer.flows.ingest_paper import ingest_paper
from paper_reviewer.flows.submit import (
    submit_create_paper_brief,
    submit_evaluate_paper_brief,
    submit_ingest_paper,
)

__all__ = [
    "create_paper_brief",
    "evaluate_paper_brief",
    "inform_full_text",
    "inform_source_record",
    "ingest_paper",
    "submit_create_paper_brief",
    "submit_evaluate_paper_brief",
    "submit_ingest_paper",
]
