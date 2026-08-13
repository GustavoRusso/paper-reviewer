"""Shared helpers for fulfill papers metadata domain tests."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.models.topic_brief_generation import create_paper
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    PaperAspectStatus,
)


def create_test_paper(
    factory: sessionmaker[Session],
    *,
    source_id: str = "pubmed",
    uid: str = "100",
    source_record_status: PaperAspectStatus = PaperAspectStatus.not_started,
    full_text_status: PaperAspectStatus = PaperAspectStatus.not_started,
    source_record_error_message: str | None = None,
    pmcid: str | None = None,
) -> int:
    session = factory()
    try:
        paper = create_paper(
            session,
            doi="10.1000/EXAMPLE",
            source_id=source_id,
            source_uid=uid,
            title="Old title",
            authors=["Old Author"],
            url="https://pubmed.ncbi.nlm.nih.gov/100/",
            journal="Old Journal",
            published_year=2020,
        )
        paper.source_record_status = source_record_status
        paper.full_text_status = full_text_status
        paper.source_record_error_message = source_record_error_message
        if source_record_status is PaperAspectStatus.succeeded:
            paper.source_record = {"abstract": {"parts": []}}
        if pmcid is not None:
            paper.pmcid = pmcid
        session.commit()
        return paper.id
    finally:
        session.close()


def mapped_photo() -> dict[str, Any]:
    return {
        "source_record": {
            "abstract": {
                "parts": [
                    {"label": "BACKGROUND", "text": "Background text."},
                    {"label": "METHODS", "text": "Methods text."},
                ],
                "copyright": None,
                "other_abstracts": [],
            },
            "dates": {
                "pub_date": {"year": 2024, "month": 3, "day": 15},
                "article_date_electronic": None,
                "date_completed": None,
                "date_revised": None,
                "history": [],
            },
            "journal_detail": {"medline_ta": "Orphanet J Rare Dis"},
            "types_language": {},
            "indexing": {},
            "funding": {},
            "coi_notes": {},
        },
        "title": "New title",
        "authors": ["Ada Lovelace"],
        "journal": "Orphanet J Rare Dis",
        "published_year": 2024,
        "pub_date": date(2024, 3, 15),
        "abstract_text": "Background text. Methods text.",
        "pmcid": None,
    }


def cloud_hit(*, is_open_access: bool = True, pdf: bool = True) -> dict[str, Any]:
    result: dict[str, Any] = {
        "pmcid": "PMC5334499",
        "pmcid_version": 2,
        "is_open_access": is_open_access,
        "full_text_plain": "Full article text from Cloud.",
        "pmc_article_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5334499/",
    }
    if pdf:
        result["open_access_pdf_url"] = (
            "https://pmc-oa-opendata.s3.amazonaws.com/PMC5334499.2/PMC5334499.2.pdf"
        )
    return result
