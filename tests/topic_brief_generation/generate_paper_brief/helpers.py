"""Shared helpers for generate paper brief domain tests."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.topic_brief_generation import create_paper
from paper_reviewer.models.topic_brief_generation.paper_brief import create_paper_brief_row
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_brief_generation.generate_paper_brief import (
    PaperBriefContent,
)


def sample_brief_content(**overrides: object) -> PaperBriefContent:
    data: dict[str, object] = {
        "summary": "The paper matters because it reports a new result.",
        "objective": "The authors aimed to close a knowledge gap.",
        "key_findings": ["Primary metric increased.", "Secondary metric held."],
    }
    data.update(overrides)
    return PaperBriefContent.model_validate(data)


def create_test_paper(
    factory: sessionmaker[Session],
    *,
    uid: str = "100",
    doi: str = "10.1000/EXAMPLE",
    full_text_status: PaperAspectStatus = PaperAspectStatus.succeeded,
    full_text_plain: str | None = "Full article text from Cloud.",
    title: str = "Example title",
    journal: str | None = "Nature",
    published_year: int | None = 2024,
) -> int:
    session = factory()
    try:
        paper = create_paper(
            session,
            doi=doi,
            source_id="pubmed",
            source_uid=uid,
            title=title,
            authors=["Old Author"],
            url=f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
            journal=journal,
            published_year=published_year,
        )
        paper.full_text_status = full_text_status
        paper.full_text_plain = full_text_plain
        session.commit()
        return paper.id
    finally:
        session.close()


def add_brief(
    factory: sessionmaker[Session],
    paper_id: int,
    *,
    status: PaperAspectStatus,
    content: PaperBriefContent | None = None,
    error_message: str | None = None,
) -> None:
    session = factory()
    try:
        row = create_paper_brief_row(
            session,
            paper_id=paper_id,
            status=status,
            error_message=error_message,
        )
        if content is not None:
            row.content = content.model_dump(mode="json")
        session.commit()
    finally:
        session.close()
