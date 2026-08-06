"""PubMed dlt source: one strategy → ESearch/ESummary → PaperCandidate yields."""

from __future__ import annotations

import dlt
from dlt.sources.rest_api import rest_api_resources

from paper_reviewer.ingest.pubmed.config import build_pubmed_rest_api_config
from paper_reviewer.ingest.pubmed.mapping import docsum_to_candidate
from paper_reviewer.ingest.pubmed.term import compile_pubmed_query
from paper_reviewer.schemas.search import PubMedStrategyOverride, SearchStrategy


@dlt.source(name="pubmed")
def pubmed(
    strategy: SearchStrategy,
    override: PubMedStrategyOverride | None = None,
    api_key: str | None = None,
):
    """Extract PubMed DocSums for one strategy and yield PaperCandidate rows.

    Composes term compilation → RESTAPIConfig → rest_api_resources → DocSum map.
    Intended for in-memory collection by related-paper search (no pipeline.run).
    """
    compiled = compile_pubmed_query(strategy, override)
    config = build_pubmed_rest_api_config(
        term=compiled.term,
        retmax=compiled.retmax,
        sort=compiled.sort,
        api_key=api_key,
    )
    strategy_id = strategy.id

    @dlt.resource(name="candidates")
    def candidates():
        for resource in rest_api_resources(config):
            if resource.name != "esummary":
                continue
            for docsum in resource:
                yield docsum_to_candidate(docsum, strategy_id=strategy_id)

    return candidates
