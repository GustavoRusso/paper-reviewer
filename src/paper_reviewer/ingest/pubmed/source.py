"""PubMed dlt source: one facet → ESearch/ESummary → PaperCandidate yields."""

from __future__ import annotations

import dlt
from dlt.sources.rest_api import rest_api_resources

from paper_reviewer.ingest.pubmed.config import build_pubmed_rest_api_config
from paper_reviewer.ingest.pubmed.mapping import docsum_to_candidate
from paper_reviewer.ingest.pubmed.term import compile_pubmed_query
from paper_reviewer.schemas.search import PubMedFacetOverride, TopicFacet


@dlt.source(name="pubmed")
def pubmed(
    facet: TopicFacet,
    override: PubMedFacetOverride | None = None,
    api_key: str | None = None,
):
    """Extract PubMed DocSums for one facet and yield PaperCandidate rows.

    Composes term compilation → RESTAPIConfig → rest_api_resources → DocSum map.
    Intended for in-memory collection by related-paper search (no pipeline.run).
    """
    compiled = compile_pubmed_query(facet, override)
    config = build_pubmed_rest_api_config(
        term=compiled.term,
        retmax=compiled.retmax,
        sort=compiled.sort,
        api_key=api_key,
    )
    facet_id = facet.id

    @dlt.resource(name="candidates")
    def candidates():
        for resource in rest_api_resources(config):
            if resource.name != "esummary":
                continue
            for docsum in resource:
                yield docsum_to_candidate(docsum, facet_id=facet_id)

    return candidates
