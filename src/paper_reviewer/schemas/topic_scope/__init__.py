"""Domain contracts for the Topic scope workflow."""

from paper_reviewer.schemas.topic_scope.search_external_sources import (
    PaperCandidate,
    PubMedFacetOverride,
    PubMedSourceOverrides,
    SearchExternalSourcesResult,
    SearchCriteria,
    SourceRun,
    SourceRunStatus,
)
from paper_reviewer.schemas.topic_scope.topic_analysis import (
    TopicAnalysisResult,
    TopicFacet,
)
from paper_reviewer.schemas.topic_scope.topic_intake import (
    TopicStatement,
    accept_topic_intake,
)

__all__ = [
    "PaperCandidate",
    "PubMedFacetOverride",
    "PubMedSourceOverrides",
    "SearchExternalSourcesResult",
    "SearchCriteria",
    "SourceRun",
    "SourceRunStatus",
    "TopicAnalysisResult",
    "TopicFacet",
    "TopicStatement",
    "accept_topic_intake",
]
