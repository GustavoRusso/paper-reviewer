"""Retrieval triage step.

Pass-through confirm gate before Paper archiving.
"""

from paper_reviewer.topic_brief_generation.retrieval_triage.confirm import (
    confirm_retrieval_triage,
)

__all__ = ["confirm_retrieval_triage"]
