"""Analyze a topic statement into an in-memory TopicAnalysisResult."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from typing import Any

from paper_reviewer.schemas.topic_brief_generation.topic_analysis import (
    TopicAnalysisResult,
    TopicFacet,
)

_WHITESPACE_RE = re.compile(r"\s+")
_MODEL_NAME = "en_core_sci_sm"
_CORE_FACET_ID = "core-concepts"
_CORE_FACET_LABEL = "Core concepts"
_CORE_FACET_INTENT = "Narrow topical match from biomedical entities"

_nlp_cache: Any | None = None


def _normalize_topic_statement(text: str) -> str:
    normalized = _WHITESPACE_RE.sub(" ", text.strip())
    if not normalized:
        raise ValueError("topic statement must not be empty after normalize")
    return normalized


def _dedupe_case_insensitive(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _concepts_from_ents(doc: Any) -> list[str]:
    return _dedupe_case_insensitive(ent.text for ent in doc.ents)


def _concepts_from_fallback_tokens(doc: Any) -> list[str]:
    candidates: list[str] = []
    for token in doc:
        if token.is_stop or not token.is_alpha:
            continue
        if len(token.text) < 3:
            continue
        candidates.append(token.text)
    return _dedupe_case_insensitive(candidates)


def _extract_concepts(doc: Any, normalized: str) -> list[str]:
    concepts = _concepts_from_ents(doc)
    if concepts:
        return concepts
    concepts = _concepts_from_fallback_tokens(doc)
    if concepts:
        return concepts
    return [normalized]


def _get_cached_nlp() -> Any:
    global _nlp_cache
    if _nlp_cache is None:
        import spacy

        _nlp_cache = spacy.load(_MODEL_NAME)
    return _nlp_cache


def analyze_topic_statement(
    text: str,
    nlp: Callable[[str], Any] | None = None,
) -> TopicAnalysisResult:
    """Extract a single core-concepts facet from topic statement text."""
    normalized = _normalize_topic_statement(text)
    pipeline = nlp if nlp is not None else _get_cached_nlp()
    doc = pipeline(normalized)
    concepts = _extract_concepts(doc, normalized)
    facet = TopicFacet(
        id=_CORE_FACET_ID,
        label=_CORE_FACET_LABEL,
        intent=_CORE_FACET_INTENT,
        concepts=concepts,
        synonyms=[],
        filters={},
        date_from=None,
        date_to=None,
        retmax=None,
    )
    return TopicAnalysisResult(facets=[facet])
