"""Retrieval triage page helpers: prerequisite guard."""

from __future__ import annotations

from uuid import uuid4

from paper_reviewer.schemas.topic_brief_generation.related_paper_search import (
    RelatedPaperSearchResult,
)
from paper_reviewer.ui.topic_intake import SEARCH_KEY
from paper_reviewer.ui.retrieval_triage import (
    CONFIRM_BUTTON_LABEL,
    triage_prerequisites_met,
)


def test_confirm_button_label_names_the_action() -> None:
    assert CONFIRM_BUTTON_LABEL == "Confirm for paper archiving"


def test_prerequisites_met_when_topic_scope_key_and_search_present() -> None:
    state = {
        SEARCH_KEY: RelatedPaperSearchResult(candidates=[], source_runs=[]),
    }

    assert triage_prerequisites_met(state, topic_scope_key=uuid4()) is True


def test_prerequisites_missing_without_topic_scope_key() -> None:
    state = {
        SEARCH_KEY: RelatedPaperSearchResult(candidates=[], source_runs=[]),
    }

    assert triage_prerequisites_met(state, topic_scope_key=None) is False


def test_prerequisites_missing_without_search_result() -> None:
    assert triage_prerequisites_met({}, topic_scope_key=uuid4()) is False
