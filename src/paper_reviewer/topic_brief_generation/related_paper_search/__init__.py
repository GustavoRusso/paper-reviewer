"""Related-paper search: merge and orchestration."""

from paper_reviewer.topic_brief_generation.related_paper_search.merge import (
    merge_candidates,
)
from paper_reviewer.topic_brief_generation.related_paper_search.orchestrate import (
    search_related_papers,
)

__all__ = ["merge_candidates", "search_related_papers"]
