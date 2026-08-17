"""Paper archiving step.

Maps ``PaperCandidate`` hits to durable create-or-reuse ``Paper`` records.
"""

from paper_reviewer.topic_scope.paper_archiving.archive import (
    archive_papers,
)
from paper_reviewer.topic_scope.paper_archiving.enqueue import (
    enqueue_ingest_papers,
)

__all__ = ["archive_papers", "enqueue_ingest_papers"]
