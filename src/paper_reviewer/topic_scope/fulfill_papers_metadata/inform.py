"""Inform source-record and full-text aspects for one Paper."""

from __future__ import annotations

import os
import random
import time
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from paper_reviewer.db import create_db_engine, create_session_factory
from paper_reviewer.ingest.pubmed.pmc_cloud import (
    stripped_full_text_plain,
    usable_full_text_plain,
)
from paper_reviewer.models.paper import Paper, get_paper_by_id
from paper_reviewer.schemas.topic_scope.fulfill_papers_metadata import (
    InformFullTextResult,
    InformSourceRecordResult,
    PaperAspectStatus,
)

FetchSourceRecord = Callable[[str, str], dict[str, Any]]
EnrichFromPmcCloud = Callable[[str | None], dict[str, Any]]

_FETCH_MAX_ATTEMPTS = 3
_FETCH_RETRY_DELAY_SECONDS = 0.5
_RATE_LIMIT_RETRY_DELAY_MIN_SECONDS = 0.5
_RATE_LIMIT_RETRY_DELAY_MAX_SECONDS = 2.0
_TERMINAL_STATUSES = {
    PaperAspectStatus.succeeded,
    PaperAspectStatus.failed,
    PaperAspectStatus.unavailable,
}


def _default_session_factory() -> sessionmaker[Session]:
    return create_session_factory(create_db_engine())


def _default_fetch_source_record(source_id: str, source_uid: str) -> dict[str, Any]:
    if source_id != "pubmed":
        raise ValueError(f"Unsupported external source for inform: {source_id}")
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
    stripped = stripped_full_text_plain(enrichment.get("full_text_plain"))
    if stripped is not None:
        paper.full_text_plain = stripped
    if enrichment.get("open_access_pdf_url"):
        paper.open_access_pdf_url = enrichment["open_access_pdf_url"]
    if enrichment.get("pmc_article_url"):
        paper.pmc_article_url = enrichment["pmc_article_url"]


def _source_result(paper: Paper) -> InformSourceRecordResult:
    return InformSourceRecordResult(
        paper_id=paper.id,
        status=paper.source_record_status,
        error_message=paper.source_record_error_message,
    )


def _full_text_result(paper: Paper) -> InformFullTextResult:
    return InformFullTextResult(
        paper_id=paper.id,
        status=paper.full_text_status,
        error_message=paper.full_text_error_message,
    )


def _missing_source_result(paper_id: int) -> InformSourceRecordResult:
    return InformSourceRecordResult(
        paper_id=paper_id,
        status=PaperAspectStatus.failed,
        error_message=f"Paper id {paper_id} not found",
    )


def _missing_full_text_result(paper_id: int) -> InformFullTextResult:
    return InformFullTextResult(
        paper_id=paper_id,
        status=PaperAspectStatus.failed,
        error_message=f"Paper id {paper_id} not found",
    )


def _mark_source_failed(
    session: Session,
    paper_id: int,
    message: str,
) -> InformSourceRecordResult:
    paper = get_paper_by_id(session, paper_id)
    if paper is not None:
        paper.source_record_status = PaperAspectStatus.failed
        paper.source_record_error_message = message
        session.commit()
        return _source_result(paper)
    return InformSourceRecordResult(
        paper_id=paper_id,
        status=PaperAspectStatus.failed,
        error_message=message,
    )


def _is_ncbi_rate_limit_error(exc: BaseException) -> bool:
    """True when the exception is an NCBI HTTP 429 / API rate limit error."""
    message = str(exc)
    return "HTTP 429" in message or "API rate limit exceeded" in message


def _rate_limit_retry_delay_seconds() -> float:
    """Random wait strictly between 0.5s and 2s before retrying a rate limit."""
    return random.uniform(
        _RATE_LIMIT_RETRY_DELAY_MIN_SECONDS + 1e-9,
        _RATE_LIMIT_RETRY_DELAY_MAX_SECONDS - 1e-9,
    )


def _fetch_with_retries(
    fetch: FetchSourceRecord,
    source_id: str,
    source_uid: str,
    session: Session,
) -> dict[str, Any]:
    last_exc: Exception | None = None
    hard_attempts = 0
    while hard_attempts < _FETCH_MAX_ATTEMPTS:
        try:
            return fetch(source_id, source_uid)
        except Exception as exc:
            session.rollback()
            if _is_ncbi_rate_limit_error(exc):
                time.sleep(_rate_limit_retry_delay_seconds())
                continue
            last_exc = exc
            hard_attempts += 1
            if hard_attempts < _FETCH_MAX_ATTEMPTS:
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


def inform_source_record(
    paper_id: int,
    *,
    force: bool = False,
    session_factory: sessionmaker[Session] | None = None,
    fetch_source_record: FetchSourceRecord | None = None,
) -> InformSourceRecordResult:
    """Load one Paper and fill the source-record aspect when it is not_started."""
    factory = session_factory or _default_session_factory()
    fetch = fetch_source_record or _default_fetch_source_record
    session = factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        if paper is None:
            return _missing_source_result(paper_id)
        if not force and paper.source_record_status in _TERMINAL_STATUSES:
            return _source_result(paper)

        if paper.source_id != "pubmed":
            paper.source_record_status = PaperAspectStatus.unavailable
            paper.source_record_error_message = None
            session.commit()
            return _source_result(paper)

        try:
            payload = _fetch_with_retries(
                fetch, paper.source_id, paper.source_uid, session
            )
        except Exception as exc:
            return _mark_source_failed(session, paper_id, str(exc))

        paper = get_paper_by_id(session, paper_id)
        if paper is None:
            return _missing_source_result(paper_id)

        try:
            apply_source_inform_payload(paper, payload)
            paper.source_record_status = PaperAspectStatus.succeeded
            paper.source_record_error_message = None
            session.commit()
        except Exception as exc:
            session.rollback()
            return _mark_source_failed(session, paper_id, str(exc))
        paper = get_paper_by_id(session, paper_id)
        assert paper is not None
        return _source_result(paper)
    finally:
        session.close()


def inform_full_text(
    paper_id: int,
    *,
    force: bool = False,
    session_factory: sessionmaker[Session] | None = None,
    enrich_from_pmc_cloud: EnrichFromPmcCloud | None = None,
) -> InformFullTextResult:
    """Load one Paper and fill the full-text aspect when it is not_started."""
    factory = session_factory or _default_session_factory()
    enrich = enrich_from_pmc_cloud or _default_enrich_from_pmc_cloud
    session = factory()
    try:
        paper = get_paper_by_id(session, paper_id)
        if paper is None:
            return _missing_full_text_result(paper_id)
        if not force and paper.full_text_status in _TERMINAL_STATUSES:
            return _full_text_result(paper)
        if paper.source_record_status is not PaperAspectStatus.succeeded:
            return _full_text_result(paper)

        pmcid = paper.pmcid
        if not pmcid:
            paper.full_text_status = PaperAspectStatus.unavailable
            paper.full_text_error_message = None
            session.commit()
            return _full_text_result(paper)

        try:
            enrichment = _enrich_with_retries(enrich, str(pmcid))
        except Exception as exc:
            paper.full_text_status = PaperAspectStatus.failed
            paper.full_text_error_message = str(exc)
            session.commit()
            return _full_text_result(paper)

        _apply_full_text_enrichment(paper, enrichment)
        stripped = stripped_full_text_plain(enrichment.get("full_text_plain"))
        if stripped is None:
            paper.full_text_plain = None
        if usable_full_text_plain(enrichment.get("full_text_plain")) is not None:
            paper.full_text_status = PaperAspectStatus.succeeded
            paper.full_text_error_message = None
        else:
            paper.full_text_status = PaperAspectStatus.unavailable
            paper.full_text_error_message = None
        session.commit()
        return _full_text_result(paper)
    finally:
        session.close()
