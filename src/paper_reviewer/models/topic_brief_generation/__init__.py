"""ORM mappings for the Topic brief generation workflow."""

from paper_reviewer.models.topic_brief_generation.generation import (
    TopicBriefGeneration,
    create_topic_brief_generation,
    get_topic_brief_generation_by_public_id,
    list_topic_brief_generations,
)
from paper_reviewer.models.topic_brief_generation.paper import (
    Paper,
    create_paper,
    get_paper_by_doi,
    get_paper_by_id,
    get_paper_by_source_handle,
)
from paper_reviewer.models.topic_brief_generation.paper_brief import (
    PaperBrief,
    create_paper_brief_row,
    get_paper_brief_by_paper_id,
)

__all__ = [
    "Paper",
    "PaperBrief",
    "TopicBriefGeneration",
    "create_paper",
    "create_paper_brief_row",
    "create_topic_brief_generation",
    "get_paper_brief_by_paper_id",
    "get_paper_by_doi",
    "get_paper_by_id",
    "get_paper_by_source_handle",
    "get_topic_brief_generation_by_public_id",
    "list_topic_brief_generations",
]
