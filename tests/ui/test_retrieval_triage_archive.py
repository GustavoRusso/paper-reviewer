"""Retrieval triage page: archive summary formatting."""

from __future__ import annotations

from datetime import UTC, datetime

from paper_reviewer.schemas.topic_brief_generation.paper_archiving import (
    ArchiveError,
    ArchiveSkip,
    ArchiveSkipReason,
    Paper,
    PaperArchivingResult,
)
from paper_reviewer.ui.retrieval_triage import format_paper_archiving_summary


def test_format_summary_empty_success() -> None:
    result = PaperArchivingResult(papers=[], skipped=[], errors=[])

    assert format_paper_archiving_summary(result) == (
        "Paper archiving finished: 0 paper(s), 0 skipped, 0 error(s)."
    )


def test_format_summary_reports_counts() -> None:
    now = datetime.now(UTC)
    result = PaperArchivingResult(
        papers=[
            Paper(
                id=1,
                created_at=now,
                doi="10.1000/A",
                source_id="pubmed",
                source_uid="1",
                title="A",
                url="https://example.com/1",
            ),
            Paper(
                id=2,
                created_at=now,
                doi="10.1000/B",
                source_id="pubmed",
                source_uid="2",
                title="B",
                url="https://example.com/2",
            ),
        ],
        skipped=[
            ArchiveSkip(
                reason=ArchiveSkipReason.missing_doi,
                source_id="pubmed",
                source_uid="3",
            )
        ],
        errors=[
            ArchiveError(
                reason="db failure",
                source_id="pubmed",
                source_uid="4",
            )
        ],
    )

    assert format_paper_archiving_summary(result) == (
        "Paper archiving finished: 2 paper(s), 1 skipped, 1 error(s)."
    )
