"""Topic analysis step: scispaCy NER → persist TopicFacet rows."""

from paper_reviewer.topic_scope.topic_analysis.analyze import (
    analyze_topic_statement,
)
from paper_reviewer.topic_scope.topic_analysis.run import (
    load_topic_analysis_result,
    run_topic_analysis,
)

__all__ = [
    "analyze_topic_statement",
    "load_topic_analysis_result",
    "run_topic_analysis",
]
