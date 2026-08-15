"""ORM mappings for the Topic brief generation workflow."""

from paper_reviewer.models.topic_brief_generation.topic_analysis import (
    TopicFacet,
    delete_topic_facets_for_scope,
    list_topic_facets_for_scope,
)
from paper_reviewer.models.topic_brief_generation.topic_scope import (
    TopicScope,
    create_topic_scope,
    get_topic_scope_by_key,
    list_topic_scopes,
)

__all__ = [
    "TopicFacet",
    "TopicScope",
    "create_topic_scope",
    "delete_topic_facets_for_scope",
    "get_topic_scope_by_key",
    "list_topic_facets_for_scope",
    "list_topic_scopes",
]
