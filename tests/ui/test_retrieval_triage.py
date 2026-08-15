"""Retrieval triage page helpers: prerequisite guard."""

from __future__ import annotations

import inspect
from uuid import uuid4

from paper_reviewer.schemas.topic_brief_generation.related_paper_search import (
    RelatedPaperSearchResult,
)
from paper_reviewer.ui.topic_intake import SEARCH_KEY, SEARCH_TOPIC_SCOPE_KEY
from paper_reviewer.ui.retrieval_triage import (
    CONFIRM_BUTTON_LABEL,
    render_retrieval_triage,
    triage_prerequisites_met,
)


def test_confirm_button_label_names_the_action() -> None:
    assert CONFIRM_BUTTON_LABEL == "Confirm for paper archiving"


def test_prerequisites_met_when_topic_scope_key_and_search_present() -> None:
    topic_scope_key = uuid4()
    state = {
        SEARCH_KEY: RelatedPaperSearchResult(candidates=[], source_runs=[]),
        SEARCH_TOPIC_SCOPE_KEY: str(topic_scope_key),
    }

    assert triage_prerequisites_met(state, topic_scope_key=topic_scope_key) is True


def test_prerequisites_missing_without_topic_scope_key() -> None:
    state = {
        SEARCH_KEY: RelatedPaperSearchResult(candidates=[], source_runs=[]),
        SEARCH_TOPIC_SCOPE_KEY: str(uuid4()),
    }

    assert triage_prerequisites_met(state, topic_scope_key=None) is False


def test_prerequisites_missing_without_search_result() -> None:
    topic_scope_key = uuid4()
    state = {SEARCH_TOPIC_SCOPE_KEY: str(topic_scope_key)}

    assert triage_prerequisites_met(state, topic_scope_key=topic_scope_key) is False


def test_prerequisites_missing_when_cached_topic_scope_key_mismatches() -> None:
    state = {
        SEARCH_KEY: RelatedPaperSearchResult(candidates=[], source_runs=[]),
        SEARCH_TOPIC_SCOPE_KEY: str(uuid4()),
    }

    assert triage_prerequisites_met(state, topic_scope_key=uuid4()) is False


def test_prerequisites_missing_without_cached_topic_scope_key() -> None:
    state = {
        SEARCH_KEY: RelatedPaperSearchResult(candidates=[], source_runs=[]),
    }

    assert triage_prerequisites_met(state, topic_scope_key=uuid4()) is False


def test_empty_state_links_to_search_scope_and_intake() -> None:
    source = inspect.getsource(render_retrieval_triage)

    assert '"related_paper_search"' in source
    assert '"topic_scope"' in source
    assert '"topic_intake"' in source
