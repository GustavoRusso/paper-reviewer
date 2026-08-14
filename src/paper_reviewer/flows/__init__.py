"""Prefect flows for paper-reviewer jobs."""

from paper_reviewer.flows.create_paper_brief import create_paper_brief
from paper_reviewer.flows.fulfill_paper_metadata import fulfill_paper_metadata
from paper_reviewer.flows.inform_full_text import inform_full_text
from paper_reviewer.flows.inform_source_record import inform_source_record
from paper_reviewer.flows.regenerate_paper import regenerate_paper
from paper_reviewer.flows.submit import (
    submit_create_paper_brief,
    submit_fulfill_paper_metadata,
    submit_regenerate_paper,
)

__all__ = [
    "create_paper_brief",
    "fulfill_paper_metadata",
    "inform_full_text",
    "inform_source_record",
    "regenerate_paper",
    "submit_create_paper_brief",
    "submit_fulfill_paper_metadata",
    "submit_regenerate_paper",
]
