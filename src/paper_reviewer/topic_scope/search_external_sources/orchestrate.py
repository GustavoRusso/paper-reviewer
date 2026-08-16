"""Search external sources orchestration: registry, collect, merge, fail-soft."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from paper_reviewer.ingest.pubmed.source import pubmed
from paper_reviewer.schemas.topic_brief_generation.search_external_sources import (
    PaperCandidate,
    PubMedFacetOverride,
    PubMedSourceOverrides,
    SearchExternalSourcesResult,
    SearchCriteria,
    SourceRun,
    SourceRunStatus,
)
from paper_reviewer.schemas.topic_brief_generation.topic_analysis import (
    TopicAnalysisResult,
)
from paper_reviewer.topic_brief_generation.search_external_sources.merge import (
    merge_candidates,
)

PaperSourceRunner = Callable[[SearchCriteria], list[PaperCandidate]]


def _collect_candidates(source: Any) -> list[PaperCandidate]:
    rows = list(source.candidates)
    return [
        row if isinstance(row, PaperCandidate) else PaperCandidate.model_validate(row)
        for row in rows
    ]


def _pubmed_override_for(
    criteria: SearchCriteria, facet_id: str
) -> PubMedFacetOverride | None:
    raw = criteria.source_overrides.get("pubmed")
    if not raw:
        return None
    overrides = PubMedSourceOverrides.model_validate(raw)
    return overrides.facets.get(facet_id)


def run_pubmed_source(
    criteria: SearchCriteria, *, api_key: str | None = None
) -> list[PaperCandidate]:
    """Run the PubMed dlt source for every facet and collect candidates."""
    collected: list[PaperCandidate] = []
    for facet in criteria.topic_analysis.facets:
        override = _pubmed_override_for(criteria, facet.id)
        source = pubmed(facet, override=override, api_key=api_key)
        collected.extend(_collect_candidates(source))
    return collected


def default_registry(*, api_key: str | None = None) -> dict[str, PaperSourceRunner]:
    """Registered external sources for search external sources."""

    def pubmed_runner(criteria: SearchCriteria) -> list[PaperCandidate]:
        return run_pubmed_source(criteria, api_key=api_key)

    return {"pubmed": pubmed_runner}


def search_external_sources(
    topic_analysis: TopicAnalysisResult,
    *,
    source_overrides: Mapping[str, Any] | None = None,
    registry: Mapping[str, PaperSourceRunner] | None = None,
    api_key: str | None = None,
) -> SearchExternalSourcesResult:
    """Run registered sources for analysis, merge candidates, fail-soft on errors."""
    criteria = SearchCriteria(
        topic_analysis=topic_analysis,
        source_overrides=dict(source_overrides or {}),
    )
    facets = criteria.topic_analysis.facets
    if not facets:
        return SearchExternalSourcesResult(
            candidates=[],
            source_runs=[],
            notes="No facets provided; nothing to search.",
        )

    runners = dict(registry) if registry is not None else default_registry(api_key=api_key)
    facet_ids = [f.id for f in facets]
    all_candidates: list[PaperCandidate] = []
    source_runs: list[SourceRun] = []

    for source_id, runner in runners.items():
        try:
            hits = runner(criteria)
        except Exception as exc:  # noqa: BLE001 — fail-soft per source
            source_runs.append(
                SourceRun(
                    source_id=source_id,
                    status=SourceRunStatus.error,
                    hit_count=0,
                    facet_ids=facet_ids,
                    error=str(exc),
                )
            )
            continue

        hit_count = len(hits)
        all_candidates.extend(hits)
        status = SourceRunStatus.ok if hit_count > 0 else SourceRunStatus.empty
        source_runs.append(
            SourceRun(
                source_id=source_id,
                status=status,
                hit_count=hit_count,
                facet_ids=facet_ids,
                error=None,
            )
        )

    return SearchExternalSourcesResult(
        candidates=merge_candidates(all_candidates),
        source_runs=source_runs,
        notes=None,
    )
