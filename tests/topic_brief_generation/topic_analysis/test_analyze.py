"""Topic analysis analyzer: fake-nlp unit tests."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from paper_reviewer.schemas.topic_brief_generation.topic_analysis import (
    TopicAnalysisResult,
    TopicFacet,
)
from paper_reviewer.topic_brief_generation.topic_analysis import analyze_topic_statement


@dataclass
class FakeSpan:
    text: str


@dataclass
class FakeToken:
    text: str
    is_stop: bool = False
    is_alpha: bool = True


@dataclass
class FakeDoc:
    ents: list[FakeSpan] = field(default_factory=list)
    tokens: list[FakeToken] = field(default_factory=list)

    def __iter__(self):
        return iter(self.tokens)


class FakeNlp:
    """Callable stand-in for a spaCy Language pipeline."""

    def __init__(self, doc: FakeDoc) -> None:
        self._doc = doc
        self.calls: list[str] = []

    def __call__(self, text: str) -> FakeDoc:
        self.calls.append(text)
        return self._doc


def test_whitespace_only_raises_value_error() -> None:
    nlp = FakeNlp(FakeDoc())
    with pytest.raises(ValueError):
        analyze_topic_statement("   \n\t  ", nlp=nlp)
    assert nlp.calls == []


def test_empty_string_raises_value_error() -> None:
    nlp = FakeNlp(FakeDoc())
    with pytest.raises(ValueError):
        analyze_topic_statement("", nlp=nlp)
    assert nlp.calls == []


def test_ents_produce_exact_concepts_and_v1_facet() -> None:
    nlp = FakeNlp(
        FakeDoc(
            ents=[FakeSpan("glioblastoma"), FakeSpan("immunotherapy")],
            tokens=[
                FakeToken("glioblastoma"),
                FakeToken("immunotherapy"),
                FakeToken("outcomes"),
            ],
        )
    )

    result = analyze_topic_statement("glioblastoma immunotherapy outcomes", nlp=nlp)

    assert isinstance(result, TopicAnalysisResult)
    assert len(result.facets) == 1
    facet = result.facets[0]
    assert isinstance(facet, TopicFacet)
    assert facet.id == "core-concepts"
    assert facet.label == "Core concepts"
    assert facet.intent == "Narrow topical match from biomedical entities"
    assert facet.concepts == ["glioblastoma", "immunotherapy"]
    assert facet.synonyms == []
    assert facet.filters == {}
    assert facet.date_from is None
    assert facet.date_to is None
    assert facet.retmax is None
    assert nlp.calls == ["glioblastoma immunotherapy outcomes"]


def test_normalize_collapses_whitespace_before_nlp() -> None:
    nlp = FakeNlp(FakeDoc(ents=[FakeSpan("glioblastoma")]))

    analyze_topic_statement("  glioblastoma\n\timmunotherapy  ", nlp=nlp)

    assert nlp.calls == ["glioblastoma immunotherapy"]


def test_case_insensitive_dedupe_keeps_first_surface_form() -> None:
    nlp = FakeNlp(
        FakeDoc(
            ents=[
                FakeSpan("Glioblastoma"),
                FakeSpan("glioblastoma"),
                FakeSpan("immunotherapy"),
            ]
        )
    )

    result = analyze_topic_statement("Glioblastoma glioblastoma immunotherapy", nlp=nlp)

    assert result.facets[0].concepts == ["Glioblastoma", "immunotherapy"]


def test_fallback_b_uses_non_stop_alpha_tokens_len_ge_3() -> None:
    nlp = FakeNlp(
        FakeDoc(
            ents=[],
            tokens=[
                FakeToken("the", is_stop=True),
                FakeToken("AI", is_alpha=True),  # len < 3
                FakeToken("outcomes", is_stop=False),
                FakeToken("research", is_stop=False),
                FakeToken("42", is_alpha=False),
                FakeToken("Outcomes", is_stop=False),  # case-insensitive dup
            ],
        )
    )

    result = analyze_topic_statement("the AI outcomes research 42 Outcomes", nlp=nlp)

    assert result.facets[0].concepts == ["outcomes", "research"]


def test_fallback_b_uses_whole_text_when_no_usable_tokens() -> None:
    nlp = FakeNlp(
        FakeDoc(
            ents=[],
            tokens=[
                FakeToken("the", is_stop=True),
                FakeToken("AI", is_stop=False, is_alpha=True),
            ],
        )
    )

    result = analyze_topic_statement("the AI", nlp=nlp)

    assert result.facets[0].concepts == ["the AI"]


def test_result_validates_as_topic_analysis_result() -> None:
    nlp = FakeNlp(FakeDoc(ents=[FakeSpan("asthma")]))
    result = analyze_topic_statement("asthma", nlp=nlp)
    revalidated: TopicAnalysisResult = TopicAnalysisResult.model_validate(
        result.model_dump()
    )
    assert revalidated.facets[0].concepts == ["asthma"]
