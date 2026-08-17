"""Evaluate a succeeded global PaperBrief with a G-Eval judge.

The judge prompt lives in ``paper_brief_evaluation_template.md``.
Behavior contract: docs/specs/2.2.4-paper-brief-evaluation.md.
"""

from paper_reviewer.topic_scope.paper_brief_evaluation.evaluate import (
    evaluate_paper_brief,
)

__all__ = [
    "evaluate_paper_brief",
]
