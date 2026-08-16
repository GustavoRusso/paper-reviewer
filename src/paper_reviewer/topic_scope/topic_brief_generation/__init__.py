"""Topic brief step: create_topic_brief + enqueue + briefed Reference gate.

Content sections and the LLM prompt live in ``topic_brief_template.md``.
Behavior contract: docs/specs/4-topic-brief-generation.md.
"""

from paper_reviewer.topic_scope.topic_brief_generation.briefed import (
    BriefedReference,
    citation_description,
    count_briefed_references,
    list_briefed_references,
)
from paper_reviewer.topic_scope.topic_brief_generation.create import (
    create_topic_brief,
)
from paper_reviewer.topic_scope.topic_brief_generation.enqueue import (
    enqueue_create_topic_brief,
)

__all__ = [
    "BriefedReference",
    "citation_description",
    "count_briefed_references",
    "create_topic_brief",
    "enqueue_create_topic_brief",
    "list_briefed_references",
]
