"""Apply source-inform payload to a Paper and run inform_paper_from_source."""

from __future__ import annotations

import os
import time
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
EnrichFromPmcCloud = Callable[[str | None], dict[str, Any]]

_FETCH_MAX_ATTEMPTS = 3
_FETCH_RETRY_DELAY_SECONDS = 0.5


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


def _default_enrich_from_pmc_cloud(pmcid: str | None) -> dict[str, Any]:
    from paper_reviewer.ingest.pubmed.pmc_cloud import fetch_pmc_cloud_enrichment

    return fetch_pmc_cloud_enrichment(pmcid)


def _merge_pmc_cloud_enrichment(
    payload: dict[str, Any],
    enrich: EnrichFromPmcCloud,
) -> None:
    """Merge Cloud fields into payload. Never raise; Cloud miss is silent."""
    pmcid = payload.get("pmcid")
    if not pmcid:
        return
    try:
        enrichment = enrich(pmcid)
    except Exception:
        return
    if enrichment:
        payload.update(enrichment)


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

    pmcid = payload.get("pmcid")
    if pmcid:
        paper.pmcid = pmcid
        paper.pmc_article_url = payload.get("pmc_article_url") or (
            f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
        )
    elif payload.get("pmc_article_url"):
        paper.pmc_article_url = payload["pmc_article_url"]

    if "pmcid_version" in payload:
        paper.pmcid_version = payload["pmcid_version"]
    if "is_open_access" in payload:
        paper.is_open_access = payload["is_open_access"]
    if payload.get("full_text_plain"):
        paper.full_text_plain = payload["full_text_plain"]
    if payload.get("open_access_pdf_url"):
        paper.open_access_pdf_url = payload["open_access_pdf_url"]

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
    enrich_from_pmc_cloud: EnrichFromPmcCloud | None = None,
) -> InformPaperFromSourceResult:
    """Load one Paper, fetch fuller source record when needed, persist result."""
    factory = session_factory or _default_session_factory()
    fetch = fetch_source_record or _default_fetch_source_record
    enrich = enrich_from_pmc_cloud or _default_enrich_from_pmc_cloud
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

        last_exc: Exception | None = None
        payload: dict[str, Any] | None = None
        for attempt in range(1, _FETCH_MAX_ATTEMPTS + 1):
            try:
                payload = fetch(paper.source_id, paper.source_uid)
                break
            except Exception as exc:
                last_exc = exc
                session.rollback()
                if attempt < _FETCH_MAX_ATTEMPTS:
                    time.sleep(_FETCH_RETRY_DELAY_SECONDS)
        if payload is None:
            return _mark_failed(session, paper_id, str(last_exc))

        try:
            _merge_pmc_cloud_enrichment(payload, enrich)
            apply_source_inform_payload(paper, payload)
            session.commit()
        except Exception as exc:
            session.rollback()
            return _mark_failed(session, paper_id, str(exc))
        return InformPaperFromSourceResult(
            paper_id=paper_id,
            outcome=InformOutcome.fulfilled,
            error_message=None,
        )
    finally:
        session.close()
