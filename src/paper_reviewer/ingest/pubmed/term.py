"""Compile generic search strategies into PubMed/Entrez query terms."""

from __future__ import annotations

from pydantic import BaseModel

from paper_reviewer.schemas.search import PubMedStrategyOverride, SearchStrategy

_OPEN_ENDED_PDAT_YEAR = "3000"


class CompiledPubmedQuery(BaseModel):
    """ESearch parameters derived from a strategy (+ optional PubMed override)."""

    term: str
    retmax: int | None = None
    sort: str | None = None


def compile_pubmed_query(
    strategy: SearchStrategy,
    override: PubMedStrategyOverride | None = None,
) -> CompiledPubmedQuery:
    """Build an Entrez ``term`` (and retmax/sort) for one strategy.

    If ``override.raw_term`` is set, that string is used as-is and structured
    compilation is skipped.
    """
    if override is not None and override.raw_term is not None:
        return CompiledPubmedQuery(
            term=override.raw_term,
            retmax=override.retmax if override.retmax is not None else strategy.retmax,
            sort=override.sort,
        )

    mesh_terms = _mesh_terms(strategy)
    clauses: list[str] = []

    for index, concept in enumerate(strategy.concepts):
        field = "Mesh" if _casefold_in(concept, mesh_terms) else "Title/Abstract"
        concept_clause = _field_term(concept, field)
        if index == 0 and strategy.synonyms:
            synonym_parts = [concept_clause, *(_field_term(s, field) for s in strategy.synonyms)]
            clauses.append(f"({' OR '.join(synonym_parts)})")
        else:
            clauses.append(concept_clause)

    for mesh in mesh_terms:
        if any(_casefold_eq(mesh, c) for c in strategy.concepts):
            continue
        clauses.append(_field_term(mesh, "Mesh"))

    date_clause = _pdat_clause(strategy.date_from, strategy.date_to)
    if date_clause is not None:
        clauses.append(date_clause)

    return CompiledPubmedQuery(
        term=" AND ".join(clauses),
        retmax=strategy.retmax,
        sort=None,
    )


def _mesh_terms(strategy: SearchStrategy) -> list[str]:
    raw = strategy.filters.get("mesh_terms", [])
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw]


def _casefold_in(value: str, options: list[str]) -> bool:
    return any(_casefold_eq(value, option) for option in options)


def _casefold_eq(left: str, right: str) -> bool:
    return left.casefold() == right.casefold()


def _field_term(term: str, field: str) -> str:
    escaped = term.replace('"', '\\"')
    return f'"{escaped}"[{field}]'


def _pdat_clause(date_from: str | None, date_to: str | None) -> str | None:
    if date_from is None and date_to is None:
        return None
    start = _year(date_from) if date_from is not None else "1000"
    end = _year(date_to) if date_to is not None else _OPEN_ENDED_PDAT_YEAR
    return f"{start}:{end}[pdat]"


def _year(date_value: str) -> str:
    return date_value[:4]
