"""Prefect flows for paper-reviewer jobs."""

from paper_reviewer.flows.inform_paper_from_source import inform_paper_from_source
from paper_reviewer.flows.submit import submit_inform_paper_from_source

__all__ = [
    "inform_paper_from_source",
    "submit_inform_paper_from_source",
]
