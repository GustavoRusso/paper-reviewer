"""Apply source-inform payload to a Paper and run inform_paper_from_source."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory
from paper_reviewer.models.topic_brief_generation.paper import Paper, get_paper_by_id
from paper_reviewer.schemas.topic_brief_generation.fulfill_papers_metadata import (
    InformOutcome,
    InformPaperFromSourceResult,
    PaperAspectStatus,
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


def _apply_full_text_enrichment(paper: Paper, enrichment: dict[str, Any]) -> None:
    if "pmcid_version" in enrichment:
        paper.pmcid_version = enrichment["pmcid_version"]
    if "is_open_access" in enrichment:
        paper.is_open_access = enrichment["is_open_access"]
    if enrichment.get("full_text_plain"):
        paper.full_text_plain = enrichment["full_text_plain"]
    if enrichment.get("open_access_pdf_url"):
        paper.open_access_pdf_url = enrichment["open_access_pdf_url"]
    if enrichment.get("pmc_article_url"):
        paper.pmc_article_url = enrichment["pmc_article_url"]


def _result_from_paper(
    paper: Paper,
    outcome: InformOutcome,
    *,
    error_message: str | None = None,
) -> InformPaperFromSourceResult:
    return InformPaperFromSourceResult(
        paper_id=paper.id,
        outcome=outcome,
        error_message=error_message,
        source_record_status=paper.source_record_status,
        full_text_status=paper.full_text_status,
        source_record_error_message=paper.source_record_error_message,
        full_text_error_message=paper.full_text_error_message,
    )


def _mark_source_failed(
    session: Session,
    paper_id: int,
    message: str,
) -> InformPaperFromSourceResult:
    paper = get_paper_by_id(session, paper_id)
    if paper is not None:
        paper.source_record_status = PaperAspectStatus.failed
        paper.source_record_error_message = message
        session.commit()
        return _result_from_paper(
            paper,
            InformOutcome.failed,
            error_message=message,
        )
    return InformPaperFromSourceResult(
        paper_id=paper_id,
        outcome=InformOutcome.failed,
        error_message=message,
        source_record_status=PaperAspectStatus.failed,
        full_text_status=PaperAspectStatus.not_started,
        source_record_error_message=message,
    )


def _fetch_with_retries(
    fetch: FetchSourceRecord,
    source_id: str,
    source_uid: str,
    session: Session,
) -> dict[str, Any]:
    last_exc: Exception | None = None
    for attempt in range(1, _FETCH_MAX_ATTEMPTS + 1):
        try:
            return fetch(source_id, source_uid)
        except Exception as exc:
            last_exc = exc
            session.rollback()
            if attempt < _FETCH_MAX_ATTEMPTS:
                time.sleep(_FETCH_RETRY_DELAY_SECONDS)
    assert last_exc is not None
    raise last_exc


def _enrich_with_retries(
    enrich: EnrichFromPmcCloud,
    pmcid: str,
) -> dict[str, Any]:
    last_exc: Exception | None = None
    for attempt in range(1, _FETCH_MAX_ATTEMPTS + 1):
        try:
            return enrich(pmcid)
        except Exception as exc:
            last_exc = exc
            if attempt < _FETCH_MAX_ATTEMPTS:
                time.sleep(_FETCH_RETRY_DELAY_SECONDS)
    assert last_exc is not None
    raise last_exc


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
                source_record_status=PaperAspectStatus.failed,
                full_text_status=PaperAspectStatus.not_started,
                source_record_error_message=f"Paper id {paper_id} not found",
            )
        if paper.source_record_status == PaperAspectStatus.succeeded:
            return _result_from_paper(paper, InformOutcome.skipped_already_informed)

        if paper.source_id != "pubmed":
            paper.source_record_status = PaperAspectStatus.unavailable
            paper.source_record_error_message = None
            session.commit()
            return _result_from_paper(paper, InformOutcome.unavailable)

        try:
            payload = _fetch_with_retries(
                fetch, paper.source_id, paper.source_uid, session
            )
        except Exception as exc:
            return _mark_source_failed(session, paper_id, str(exc))

        paper = get_paper_by_id(session, paper_id)
        if paper is None:
            return InformPaperFromSourceResult(
                paper_id=paper_id,
                outcome=InformOutcome.failed,
                error_message=f"Paper id {paper_id} not found",
                source_record_status=PaperAspectStatus.failed,
                full_text_status=PaperAspectStatus.not_started,
            )

        try:
            apply_source_inform_payload(paper, payload)
            paper.source_record_status = PaperAspectStatus.succeeded
            paper.source_record_error_message = None

            pmcid = payload.get("pmcid")
            if not pmcid:
                paper.full_text_status = PaperAspectStatus.unavailable
                paper.full_text_error_message = None
            else:
                try:
                    enrichment = _enrich_with_retries(enrich, str(pmcid))
                except Exception as exc:
                    paper.full_text_status = PaperAspectStatus.failed
                    paper.full_text_error_message = str(exc)
                else:
                    if enrichment.get("full_text_plain"):
                        _apply_full_text_enrichment(paper, enrichment)
                        paper.full_text_status = PaperAspectStatus.succeeded
                        paper.full_text_error_message = None
                    else:
                        paper.full_text_status = PaperAspectStatus.unavailable
                        paper.full_text_error_message = None
            session.commit()
        except Exception as exc:
            session.rollback()
            return _mark_source_failed(session, paper_id, str(exc))
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        return _result_from_paper(paper, InformOutcome.fulfilled)
    finally:
        session.close()
