"""Domain contracts for the Topic brief generation workflow."""

from paper_reviewer.schemas.topic_brief_generation.related_paper_search import (
    PaperCandidate,
    PubMedFacetOverride,
    PubMedSourceOverrides,
    RelatedPaperSearchResult,
    SearchCriteria,
    SourceRun,
    SourceRunStatus,
)
from paper_reviewer.schemas.topic_brief_generation.topic_analysis import (
    TopicAnalysisResult,
    TopicFacet,
)
from paper_reviewer.schemas.topic_brief_generation.topic_intake import (
    TopicStatement,
    accept_topic_intake,
)

__all__ = [
    "PaperCandidate",
    "PubMedFacetOverride",
    "PubMedSourceOverrides",
    "RelatedPaperSearchResult",
    "SearchCriteria",
    "SourceRun",
    "SourceRunStatus",
    "TopicAnalysisResult",
    "TopicFacet",
    "TopicStatement",
    "accept_topic_intake",
]
