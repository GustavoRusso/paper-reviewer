"""Retrieval triage page helpers: prerequisite guard."""

from __future__ import annotations

import uuid

from paper_reviewer.schemas.topic_brief_generation.related_paper_search import (
    RelatedPaperSearchResult,
)
from paper_reviewer.ui.retrieval_triage import triage_prerequisites_met
from paper_reviewer.ui.topic_intake import PUBLIC_ID_KEY, SEARCH_KEY


def test_prerequisites_met_when_public_id_and_search_present() -> None:
    state = {
        PUBLIC_ID_KEY: uuid.uuid4(),
        SEARCH_KEY: RelatedPaperSearchResult(candidates=[], source_runs=[]),
    }

    assert triage_prerequisites_met(state) is True


def test_prerequisites_missing_without_public_id() -> None:
    state = {
        SEARCH_KEY: RelatedPaperSearchResult(candidates=[], source_runs=[]),
    }

    assert triage_prerequisites_met(state) is False


def test_prerequisites_missing_without_search_result() -> None:
    state = {PUBLIC_ID_KEY: uuid.uuid4()}

    assert triage_prerequisites_met(state) is False
