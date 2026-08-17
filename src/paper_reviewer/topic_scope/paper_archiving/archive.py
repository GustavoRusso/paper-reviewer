"""Create or reuse Paper records from search external sources candidates."""

from __future__ import annotations

from sqlalchemy.orm import Session

from paper_reviewer.models.paper import (
    Paper as OrmPaper,
    create_paper,
    get_paper_by_doi,
    get_paper_by_source_handle,
)
from paper_reviewer.schemas.topic_scope.paper_archiving import (
    ArchiveError,
    ArchiveSkip,
    ArchiveSkipReason,
    Paper,
    PaperArchivingResult,
)
from paper_reviewer.schemas.topic_scope.search_external_sources import (
    PaperCandidate,
)


def _is_blank(value: str | None) -> bool:
    return value is None or not str(value).strip()


def _to_read_model(row: OrmPaper) -> Paper:
    return Paper(
        id=row.id,
        created_at=row.created_at,
        doi=row.doi,
        source_id=row.source_id,
        source_uid=row.source_uid,
        title=row.title,
        authors=list(row.authors),
        journal=row.journal,
        published_year=row.published_year,
        url=row.url,
    )


def _identity_key(
    source_id: str | None,
    source_uid: str | None,
) -> tuple[str, str] | None:
    if _is_blank(source_id) or _is_blank(source_uid):
        return None
    assert source_id is not None and source_uid is not None
    return (source_id.strip(), source_uid.strip())


def archive_papers(
    session: Session,
    candidates: list[PaperCandidate],
) -> PaperArchivingResult:
    """Map candidates to create-or-reuse Paper rows (caller owns commit)."""
    papers: list[Paper] = []
    skipped: list[ArchiveSkip] = []
    errors: list[ArchiveError] = []
    created_paper_ids: list[int] = []

    resolved: dict[tuple[str, str], Paper] = {}
    seen_skip: set[tuple[str, str]] = set()
    seen_error: set[tuple[str, str]] = set()

    def record_skip(
        reason: ArchiveSkipReason,
        *,
        source_id: str | None,
        source_uid: str | None,
        doi: str | None,
    ) -> None:
        key = _identity_key(source_id, source_uid)
        if key is not None:
            if key in seen_skip or key in resolved or key in seen_error:
                return
            seen_skip.add(key)
        skipped.append(
            ArchiveSkip(
                reason=reason,
                source_id=None if _is_blank(source_id) else source_id.strip(),
                source_uid=None if _is_blank(source_uid) else source_uid.strip(),
                doi=doi,
            )
        )

    def record_error(
        reason: str,
        *,
        source_id: str | None,
        source_uid: str | None,
        doi: str | None,
    ) -> None:
        key = _identity_key(source_id, source_uid)
        if key is not None:
            if key in seen_error or key in resolved or key in seen_skip:
                return
            seen_error.add(key)
        errors.append(
            ArchiveError(
                reason=reason,
                source_id=None if _is_blank(source_id) else source_id.strip(),
                source_uid=None if _is_blank(source_uid) else source_uid.strip(),
                doi=doi,
            )
        )

    for candidate in candidates:
        raw_source_id = candidate.source_id
        raw_source_uid = candidate.source_uid
        key = _identity_key(raw_source_id, raw_source_uid)

        if key is not None and key in resolved:
            continue
        if key is not None and (key in seen_skip or key in seen_error):
            continue

        if _is_blank(candidate.doi):
            record_skip(
                ArchiveSkipReason.missing_doi,
                source_id=raw_source_id,
                source_uid=raw_source_uid,
                doi=None,
            )
            continue

        if (
            _is_blank(raw_source_id)
            or _is_blank(raw_source_uid)
            or _is_blank(candidate.title)
            or _is_blank(candidate.url)
        ):
            record_skip(
                ArchiveSkipReason.invalid_required_field,
                source_id=raw_source_id,
                source_uid=raw_source_uid,
                doi=candidate.doi.strip().upper() if not _is_blank(candidate.doi) else None,
            )
            continue

        assert key is not None
        source_id, source_uid = key
        doi = candidate.doi.strip().upper()

        try:
            with session.begin_nested():
                existing = get_paper_by_source_handle(session, source_id, source_uid)
                if existing is None:
                    doi_owner = get_paper_by_doi(session, doi)
                    if doi_owner is not None:
                        record_skip(
                            ArchiveSkipReason.doi_conflict,
                            source_id=source_id,
                            source_uid=source_uid,
                            doi=doi,
                        )
                        continue
                    row = create_paper(
                        session,
                        doi=doi,
                        source_id=source_id,
                        source_uid=source_uid,
                        title=candidate.title.strip(),
                        authors=list(candidate.authors),
                        url=candidate.url.strip(),
                        journal=candidate.journal,
                        published_year=candidate.published_year,
                    )
                    session.flush()
                    read = _to_read_model(row)
                    created_paper_ids.append(read.id)
                elif existing.doi == doi:
                    read = _to_read_model(existing)
                else:
                    doi_owner = get_paper_by_doi(session, doi)
                    if doi_owner is not None and doi_owner.id != existing.id:
                        record_skip(
                            ArchiveSkipReason.doi_conflict,
                            source_id=source_id,
                            source_uid=source_uid,
                            doi=doi,
                        )
                        continue
                    existing.doi = doi
                    session.flush()
                    read = _to_read_model(existing)

                resolved[key] = read
                papers.append(read)
        except Exception as exc:  # noqa: BLE001 — fail-soft per candidate
            record_error(
                str(exc),
                source_id=source_id,
                source_uid=source_uid,
                doi=doi,
            )

    return PaperArchivingResult(
        papers=papers,
        skipped=skipped,
        errors=errors,
        created_paper_ids=created_paper_ids,
    )
