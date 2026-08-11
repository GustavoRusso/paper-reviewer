"""Paper archiving: Pydantic read model and result contracts."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from paper_reviewer.schemas.topic_brief_generation.paper_archiving import (
    ArchiveError,
    ArchiveSkip,
    ArchiveSkipReason,
    Paper,
    PaperArchivingResult,
)


def _sample_paper(**overrides: object) -> Paper:
    data: dict[str, object] = {
        "id": 1,
        "created_at": datetime(2026, 8, 10, tzinfo=timezone.utc),
        "doi": "10.1000/EXAMPLE",
        "source_id": "pubmed",
        "source_uid": "12345",
        "title": "Example title",
        "authors": ["Ada Lovelace"],
        "journal": "Nature",
        "published_year": 2024,
        "url": "https://pubmed.ncbi.nlm.nih.gov/12345/",
    }
    data.update(overrides)
    return Paper.model_validate(data)


def test_paper_construction() -> None:
    paper = _sample_paper()

    assert paper.id == 1
    assert paper.doi == "10.1000/EXAMPLE"
    assert paper.authors == ["Ada Lovelace"]
    assert paper.journal == "Nature"


def test_paper_allows_empty_authors_and_optional_fields() -> None:
    paper = _sample_paper(authors=[], journal=None, published_year=None)

    assert paper.authors == []
    assert paper.journal is None
    assert paper.published_year is None


def test_paper_requires_identity_and_bibliographic_fields() -> None:
    with pytest.raises(ValidationError):
        Paper.model_validate(
            {
                "id": 1,
                "created_at": datetime(2026, 8, 10, tzinfo=timezone.utc),
                "doi": "10.1000/EXAMPLE",
                "source_id": "pubmed",
                "source_uid": "12345",
                "title": "Example title",
                "authors": [],
            }
        )


def test_archive_skip_reason_values() -> None:
    assert ArchiveSkipReason.missing_doi.value == "missing_doi"
    assert ArchiveSkipReason.invalid_required_field.value == "invalid_required_field"
    assert ArchiveSkipReason.doi_conflict.value == "doi_conflict"


def test_paper_archiving_result_defaults_to_empty_lists() -> None:
    result = PaperArchivingResult()

    assert result.papers == []
    assert result.skipped == []
    assert result.errors == []


def test_paper_archiving_result_holds_papers_skips_and_errors() -> None:
    paper = _sample_paper()
    skipped = ArchiveSkip(
        reason=ArchiveSkipReason.missing_doi,
        source_id="pubmed",
        source_uid="9",
        doi=None,
    )
    error = ArchiveError(
        reason="flush failed",
        source_id="pubmed",
        source_uid="8",
        doi="10.1000/X",
    )

    result = PaperArchivingResult(
        papers=[paper],
        skipped=[skipped],
        errors=[error],
    )

    assert result.papers == [paper]
    assert result.skipped == [skipped]
    assert result.errors == [error]
