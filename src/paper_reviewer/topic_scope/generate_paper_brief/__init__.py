"""Generate paper brief step: global PaperBrief from full text.

Content sections and the LLM prompt live in ``paper_brief_template.md``.
Behavior contract: docs/specs/2.2.3-generate-paper-brief.md.
"""

from paper_reviewer.topic_scope.generate_paper_brief.create import (
    create_paper_brief,
)
from paper_reviewer.topic_scope.generate_paper_brief.enqueue import (
    enqueue_generate_paper_briefs,
    needs_create_paper_brief,
)

__all__ = [
    "create_paper_brief",
    "enqueue_generate_paper_briefs",
    "needs_create_paper_brief",
]
