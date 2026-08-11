"""Paper archiving step.

Maps ``PaperCandidate`` hits to durable create-or-reuse ``Paper`` records.
"""

from paper_reviewer.topic_brief_generation.paper_archiving.archive import (
    archive_papers,
)

__all__ = ["archive_papers"]
