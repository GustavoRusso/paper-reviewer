"""Paper archiving page helpers: prerequisites and display formatting."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from paper_reviewer.schemas.topic_scope.paper_archiving import (
    ArchiveError,
    ArchiveSkip,
    ArchiveSkipReason,
    Paper,
    PaperArchivingResult,
)
from paper_reviewer.schemas.topic_scope.search_external_sources import (
    SearchExternalSourcesResult,
)
from paper_reviewer.ui.paper_archiving import (
    archive_skip_reason_label,
    archiving_prerequisites_met,
    format_archived_paper_caption,
    format_paper_archiving_summary,
)
from paper_reviewer.ui.topic_intake import SEARCH_KEY, SEARCH_TOPIC_SCOPE_KEY


def test_prerequisites_met_when_search_cache_matches() -> None:
    topic_scope_key = uuid4()
    state = {
        SEARCH_KEY: SearchExternalSourcesResult(candidates=[], source_runs=[]),
        SEARCH_TOPIC_SCOPE_KEY: str(topic_scope_key),
    }

    assert archiving_prerequisites_met(state, topic_scope_key=topic_scope_key) is True


def test_prerequisites_missing_without_search_result() -> None:
    assert archiving_prerequisites_met({}, topic_scope_key=uuid4()) is False


def test_prerequisites_missing_when_topic_scope_key_mismatches() -> None:
    state = {
        SEARCH_KEY: SearchExternalSourcesResult(candidates=[], source_runs=[]),
        SEARCH_TOPIC_SCOPE_KEY: str(uuid4()),
    }

    assert archiving_prerequisites_met(state, topic_scope_key=uuid4()) is False


def test_archive_skip_reason_labels() -> None:
    assert archive_skip_reason_label(ArchiveSkipReason.missing_doi) == "Missing DOI"
    assert (
        archive_skip_reason_label(ArchiveSkipReason.invalid_required_field)
        == "Invalid required field"
    )
    assert archive_skip_reason_label(ArchiveSkipReason.doi_conflict) == "DOI conflict"


def test_format_archived_paper_caption() -> None:
    paper = Paper(
        id=1,
        created_at=datetime(2026, 8, 11, 12, 0, 0, tzinfo=UTC),
        doi="10.1000/A",
        source_id="pubmed",
        source_uid="123",
        title="Example",
        authors=["Ada Lovelace", "Alan Turing"],
        journal="Nature",
        published_year=2024,
        url="https://example.com/1",
    )

    assert format_archived_paper_caption(paper) == (
        "Ada Lovelace, Alan Turing · Nature · 2024 · DOI `10.1000/A` · "
        "`pubmed` / `123` · 2026-08-11T12:00:00+00:00"
    )


def test_format_archived_paper_caption_missing_optional_fields() -> None:
    paper = Paper(
        id=1,
        created_at=datetime(2026, 8, 11, 12, 0, 0, tzinfo=UTC),
        doi="10.1000/B",
        source_id="pubmed",
        source_uid="456",
        title="Example",
        url="https://example.com/2",
    )

    assert format_archived_paper_caption(paper) == (
        "— · — · — · DOI `10.1000/B` · "
        "`pubmed` / `456` · 2026-08-11T12:00:00+00:00"
    )


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
