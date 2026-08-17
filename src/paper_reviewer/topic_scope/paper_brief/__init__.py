"""Paper brief reader: load a succeeded global PaperBrief by DOI.

Behavior contract: docs/specs/paper-brief.md.
"""

from paper_reviewer.topic_scope.paper_brief.load import (
    load_paper_brief_for_read,
)

__all__ = ["load_paper_brief_for_read"]
