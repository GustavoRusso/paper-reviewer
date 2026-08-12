"""ORM mappings for the Topic brief generation workflow."""

from paper_reviewer.models.topic_brief_generation.generation import (
    TopicBriefGeneration,
    create_topic_brief_generation,
    get_topic_brief_generation_by_public_id,
)
from paper_reviewer.models.topic_brief_generation.paper import (
    Paper,
    create_paper,
    get_paper_by_doi,
    get_paper_by_id,
    get_paper_by_source_handle,
)

__all__ = [
    "Paper",
    "TopicBriefGeneration",
    "create_paper",
    "create_topic_brief_generation",
    "get_paper_by_doi",
    "get_paper_by_id",
    "get_paper_by_source_handle",
    "get_topic_brief_generation_by_public_id",
]
