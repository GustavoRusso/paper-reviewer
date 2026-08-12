"""Apply source-inform payload to a Paper and run inform_paper_from_source."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory
from paper_reviewer.models.topic_brief_generation.paper import Paper, get_paper_by_id
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    InformOutcome,
    InformPaperFromSourceResult,
)

FetchSourceRecord = Callable[[str, str], dict[str, Any]]


def _default_session_factory() -> sessionmaker[Session]:
    return create_session_factory(create_db_engine())


def _default_fetch_source_record(source_id: str, source_uid: str) -> dict[str, Any]:
    if source_id != "pubmed":
        raise ValueError(f"Unsupported paper source for inform: {source_id}")
    from paper_reviewer.ingest.pubmed.efetch import fetch_pubmed_source_record

    return fetch_pubmed_source_record(
        source_uid,
        api_key=os.environ.get("NCBI_API_KEY") or None,
    )


def apply_source_inform_payload(paper: Paper, payload: dict[str, Any]) -> None:
    """Write mapped source photo and typed promotes onto ``paper``."""
    paper.source_record = payload["source_record"]
    title = payload.get("title")
    if title:
        paper.title = title
    authors = payload.get("authors")
    if authors:
        paper.authors = list(authors)
    journal = payload.get("journal")
    if journal:
        paper.journal = journal
    published_year = payload.get("published_year")
    if published_year is not None:
        paper.published_year = published_year
    pub_date = payload.get("pub_date")
    if pub_date is not None:
        paper.pub_date = pub_date
    abstract_text = payload.get("abstract_text")
    if abstract_text:
        paper.abstract_text = abstract_text
    paper.source_informed_at = datetime.now(UTC)
    paper.source_inform_error_message = None


def _mark_failed(
    session: Session,
    paper_id: int,
    message: str,
) -> InformPaperFromSourceResult:
    paper = get_paper_by_id(session, paper_id)
    if paper is not None:
        paper.source_inform_error_message = message
        paper.source_informed_at = None
        session.commit()
    return InformPaperFromSourceResult(
        paper_id=paper_id,
        outcome=InformOutcome.failed,
        error_message=message,
    )


def inform_paper_from_source(
    paper_id: int,
    *,
    session_factory: sessionmaker[Session] | None = None,
    fetch_source_record: FetchSourceRecord | None = None,
) -> InformPaperFromSourceResult:
    """Load one Paper, fetch fuller source record when needed, persist result."""
    factory = session_factory or _default_session_factory()
    fetch = fetch_source_record or _default_fetch_source_record
    session = factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        if paper is None:
            return InformPaperFromSourceResult(
                paper_id=paper_id,
                outcome=InformOutcome.failed,
                error_message=f"Paper id {paper_id} not found",
            )
        if paper.source_informed_at is not None:
            return InformPaperFromSourceResult(
                paper_id=paper_id,
                outcome=InformOutcome.skipped_already_informed,
                error_message=None,
            )

        if paper.source_id != "pubmed":
            return _mark_failed(
                session,
                paper_id,
                f"Unsupported paper source for inform: {paper.source_id}",
            )

        try:
            payload = fetch(paper.source_id, paper.source_uid)
            apply_source_inform_payload(paper, payload)
            session.commit()
            return InformPaperFromSourceResult(
                paper_id=paper_id,
                outcome=InformOutcome.fulfilled,
                error_message=None,
            )
        except Exception as exc:
            session.rollback()
            return _mark_failed(session, paper_id, str(exc))
    finally:
        session.close()
