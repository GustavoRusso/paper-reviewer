"""Retrieval triage page helpers: prerequisite guard."""

from __future__ import annotations

from uuid import uuid4

from paper_reviewer.schemas.topic_brief_generation.related_paper_search import (
    RelatedPaperSearchResult,
)
from paper_reviewer.ui.new_topic_brief import SEARCH_KEY
from paper_reviewer.ui.retrieval_triage import (
    CONFIRM_BUTTON_LABEL,
    triage_prerequisites_met,
)


def test_confirm_button_label_names_the_action() -> None:
    assert CONFIRM_BUTTON_LABEL == "Confirm for paper archiving"


def test_prerequisites_met_when_public_id_and_search_present() -> None:
    state = {
        SEARCH_KEY: RelatedPaperSearchResult(candidates=[], source_runs=[]),
    }

    assert triage_prerequisites_met(state, public_id=uuid4()) is True


def test_prerequisites_missing_without_public_id() -> None:
    state = {
        SEARCH_KEY: RelatedPaperSearchResult(candidates=[], source_runs=[]),
    }

    assert triage_prerequisites_met(state, public_id=None) is False


def test_prerequisites_missing_without_search_result() -> None:
    assert triage_prerequisites_met({}, public_id=uuid4()) is False
