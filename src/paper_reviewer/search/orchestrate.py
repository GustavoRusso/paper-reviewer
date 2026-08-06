"""Related-paper search orchestration: registry, collect, merge, fail-soft."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from paper_reviewer.ingest.pubmed.source import pubmed
from paper_reviewer.schemas.candidate import PaperCandidate
from paper_reviewer.schemas.search import (
    PubMedSourceOverrides,
    PubMedStrategyOverride,
    RelatedPaperSearchResult,
    SearchCriteria,
    SourceRun,
    SourceRunStatus,
)
from paper_reviewer.search.merge import merge_candidates

PaperSourceRunner = Callable[[SearchCriteria], list[PaperCandidate]]


def _collect_candidates(source: Any) -> list[PaperCandidate]:
    rows = list(source.candidates)
    return [
        row if isinstance(row, PaperCandidate) else PaperCandidate.model_validate(row)
        for row in rows
    ]


def _pubmed_override_for(
    criteria: SearchCriteria, strategy_id: str
) -> PubMedStrategyOverride | None:
    raw = criteria.source_overrides.get("pubmed")
    if not raw:
        return None
    overrides = PubMedSourceOverrides.model_validate(raw)
    return overrides.strategies.get(strategy_id)


def run_pubmed_source(
    criteria: SearchCriteria, *, api_key: str | None = None
) -> list[PaperCandidate]:
    """Run the PubMed dlt source for every strategy and collect candidates."""
    collected: list[PaperCandidate] = []
    for strategy in criteria.strategies:
        override = _pubmed_override_for(criteria, strategy.id)
        source = pubmed(strategy, override=override, api_key=api_key)
        collected.extend(_collect_candidates(source))
    return collected


def default_registry(*, api_key: str | None = None) -> dict[str, PaperSourceRunner]:
    """Registered paper sources for related-paper search."""

    def pubmed_runner(criteria: SearchCriteria) -> list[PaperCandidate]:
        return run_pubmed_source(criteria, api_key=api_key)

    return {"pubmed": pubmed_runner}


def search_related_papers(
    criteria: SearchCriteria,
    *,
    registry: Mapping[str, PaperSourceRunner] | None = None,
    api_key: str | None = None,
) -> RelatedPaperSearchResult:
    """Run registered sources for criteria, merge candidates, fail-soft on errors."""
    if not criteria.strategies:
        return RelatedPaperSearchResult(
            candidates=[],
            source_runs=[],
            notes="No strategies provided; nothing to search.",
        )

    runners = dict(registry) if registry is not None else default_registry(api_key=api_key)
    strategy_ids = [s.id for s in criteria.strategies]
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
                    strategy_ids=strategy_ids,
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
                strategy_ids=strategy_ids,
                error=None,
            )
        )

    return RelatedPaperSearchResult(
        candidates=merge_candidates(all_candidates),
        source_runs=source_runs,
        notes=None,
    )
