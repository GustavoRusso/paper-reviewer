"""TopicFacet parsing and PubMed Entrez term compilation."""

from __future__ import annotations

from paper_reviewer.ingest.pubmed.term import compile_pubmed_query
from paper_reviewer.schemas.search import PubMedFacetOverride, TopicFacet


def test_topic_facet_parses_spec_fixture_fields() -> None:
    facet = TopicFacet.model_validate(
        {
            "id": "core-concepts",
            "label": "Core concepts",
            "intent": "Narrow topical match",
            "concepts": ["glioblastoma", "immunotherapy"],
            "synonyms": ["GBM"],
            "date_from": "2018-01-01",
            "date_to": None,
            "filters": {},
            "retmax": 50,
        }
    )
    assert facet.id == "core-concepts"
    assert facet.label == "Core concepts"
    assert facet.concepts == ["glioblastoma", "immunotherapy"]
    assert facet.synonyms == ["GBM"]
    assert facet.date_from == "2018-01-01"
    assert facet.date_to is None
    assert facet.retmax == 50


def test_pubmed_override_parses_raw_term_fixture() -> None:
    override = PubMedFacetOverride.model_validate(
        {
            "raw_term": (
                "glioblastoma[mesh] AND immunotherapy[Title/Abstract] AND 2018:3000[pdat]"
            ),
            "retmax": 50,
            "sort": "relevance",
        }
    )
    assert override.raw_term.startswith("glioblastoma[mesh]")
    assert override.retmax == 50
    assert override.sort == "relevance"


def test_raw_term_override_skips_structured_compilation() -> None:
    facet = TopicFacet.model_validate(
        {
            "id": "core-concepts",
            "label": "Core concepts",
            "concepts": ["ignored-concept"],
            "retmax": 10,
        }
    )
    raw = "asthma[mesh] AND leukotrienes[mesh] AND 2009[pdat]"
    override = PubMedFacetOverride(raw_term=raw, retmax=20, sort="relevance")

    compiled = compile_pubmed_query(facet, override)

    assert compiled.term == raw
    assert compiled.retmax == 20
    assert compiled.sort == "relevance"


def test_concepts_and_synonyms_compile_with_uppercase_operators() -> None:
    facet = TopicFacet.model_validate(
        {
            "id": "core-concepts",
            "label": "Core concepts",
            "concepts": ["glioblastoma", "immunotherapy"],
            "synonyms": ["GBM"],
        }
    )

    compiled = compile_pubmed_query(facet)

    assert "AND" in compiled.term
    assert "OR" in compiled.term
    assert "and" not in compiled.term
    assert "or" not in compiled.term
    assert '"glioblastoma"[Title/Abstract]' in compiled.term
    assert '"GBM"[Title/Abstract]' in compiled.term
    assert '"immunotherapy"[Title/Abstract]' in compiled.term
    # Synonyms fold into the first concept clause
    assert compiled.term.startswith('("glioblastoma"[Title/Abstract] OR "GBM"[Title/Abstract])')


def test_date_from_only_compiles_open_ended_pdat_range() -> None:
    facet = TopicFacet.model_validate(
        {
            "id": "dated",
            "label": "Dated",
            "concepts": ["CRISPR"],
            "date_from": "2018-01-01",
            "date_to": None,
        }
    )

    compiled = compile_pubmed_query(facet)

    assert compiled.term.endswith("AND 2018:3000[pdat]")
    assert '"CRISPR"[Title/Abstract]' in compiled.term


def test_date_from_and_to_compiles_closed_pdat_range() -> None:
    facet = TopicFacet.model_validate(
        {
            "id": "dated",
            "label": "Dated",
            "concepts": ["asthma"],
            "date_from": "2018-06-01",
            "date_to": "2024-12-31",
        }
    )

    compiled = compile_pubmed_query(facet)

    assert "2018:2024[pdat]" in compiled.term


def test_mesh_terms_filter_uses_mesh_field_and_ignores_unknown_filters() -> None:
    facet = TopicFacet.model_validate(
        {
            "id": "mesh-facet",
            "label": "MeSH",
            "concepts": ["glioblastoma", "immunotherapy"],
            "filters": {
                "mesh_terms": ["glioblastoma"],
                "unknown_vendor_key": "ignore-me",
            },
        }
    )

    compiled = compile_pubmed_query(facet)

    assert '"glioblastoma"[Mesh]' in compiled.term
    assert '"immunotherapy"[Title/Abstract]' in compiled.term
    assert "unknown_vendor_key" not in compiled.term
    assert "ignore-me" not in compiled.term


def test_retmax_comes_from_facet_when_override_omits_it() -> None:
    facet = TopicFacet.model_validate(
        {
            "id": "fixture-narrow",
            "label": "Fixture narrow",
            "concepts": ["CRISPR", "base editing"],
            "retmax": 20,
        }
    )

    compiled = compile_pubmed_query(facet)

    assert compiled.retmax == 20
    assert compiled.sort is None


def test_empty_concepts_with_only_mesh_filter_still_compiles() -> None:
    facet = TopicFacet.model_validate(
        {
            "id": "mesh-only",
            "label": "MeSH only",
            "concepts": [],
            "filters": {"mesh_terms": ["asthma", "leukotrienes"]},
            "date_from": "2009-01-01",
            "date_to": "2009-12-31",
        }
    )

    compiled = compile_pubmed_query(facet)

    assert '"asthma"[Mesh]' in compiled.term
    assert '"leukotrienes"[Mesh]' in compiled.term
    assert "AND" in compiled.term
    assert "2009:2009[pdat]" in compiled.term
