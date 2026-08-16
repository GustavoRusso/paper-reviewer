"""Shared Pydantic domain contracts."""

from paper_reviewer.schemas.topic_scope import (
    PaperCandidate,
    PubMedFacetOverride,
    PubMedSourceOverrides,
    SearchExternalSourcesResult,
    SearchCriteria,
    SourceRun,
    SourceRunStatus,
    TopicAnalysisResult,
    TopicFacet,
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
