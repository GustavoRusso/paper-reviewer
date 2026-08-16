"""Search external sources: merge and orchestration."""

from paper_reviewer.topic_scope.search_external_sources.merge import (
    merge_candidates,
)
from paper_reviewer.topic_scope.search_external_sources.orchestrate import (
    search_external_sources,
)

__all__ = ["merge_candidates", "search_external_sources"]
