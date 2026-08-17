"""Shared helpers for generate paper brief domain tests."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.paper import create_paper
from paper_reviewer.models.paper_brief import create_paper_brief_row
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    PaperAspectStatus,
)
from paper_reviewer.schemas.topic_scope.generate_paper_brief import (
    PaperBriefContent,
    PaperBriefLlmResult,
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


def sample_llm_result(
    content: PaperBriefContent | None = None,
    *,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
) -> PaperBriefLlmResult:
    return PaperBriefLlmResult(
        content=content if content is not None else sample_brief_content(),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )


def add_brief(
    factory: sessionmaker[Session],
    paper_id: int,
    *,
    status: PaperAspectStatus,
    content: PaperBriefContent | None = None,
    error_message: str | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
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
        row.prompt_tokens = prompt_tokens
        row.completion_tokens = completion_tokens
        row.total_tokens = total_tokens
        session.commit()
    finally:
        session.close()
