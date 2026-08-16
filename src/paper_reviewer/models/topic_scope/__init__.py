"""ORM mappings for the Topic scope workflow."""

from paper_reviewer.models.topic_scope.reference import (
    Reference,
    create_reference,
    list_references_for_scope,
)
from paper_reviewer.models.topic_scope.topic_analysis import (
    TopicFacet,
    delete_topic_facets_for_scope,
    list_topic_facets_for_scope,
)
from paper_reviewer.models.topic_scope.topic_brief import (
    TopicBrief,
    create_topic_brief_row,
    get_topic_brief_by_topic_scope_id,
)
from paper_reviewer.models.topic_scope.topic_scope import (
    TopicScope,
    create_topic_scope,
    get_topic_scope_by_key,
    list_topic_scopes,
)

__all__ = [
    "Reference",
    "TopicBrief",
    "TopicFacet",
    "TopicScope",
    "create_reference",
    "create_topic_brief_row",
    "create_topic_scope",
    "delete_topic_facets_for_scope",
    "get_topic_brief_by_topic_scope_id",
    "get_topic_scope_by_key",
    "list_references_for_scope",
    "list_topic_facets_for_scope",
    "list_topic_scopes",
]
