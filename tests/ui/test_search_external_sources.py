"""Search external sources page: registration, cache helpers, and DB-facet input."""

from __future__ import annotations

import inspect
from uuid import uuid4

from paper_reviewer.schemas.topic_brief_generation.search_external_sources import (
    SearchExternalSourcesResult,
)
from paper_reviewer.ui.navigation import build_app_pages
from paper_reviewer.ui.search_external_sources import (
    CONTINUE_TO_PAPER_ARCHIVING_LABEL,
    GO_TO_TOPIC_ANALYSIS_LABEL,
    GO_TO_TOPIC_SCOPE_LABEL,
    MISSING_PREREQUISITES_MESSAGE,
    clear_downstream_ingest_caches,
    render_search_external_sources,
    search_cache_matches,
)
from paper_reviewer.ui.topic_intake import (
    ANALYSIS_KEY,
    ARCHIVING_RESULT_KEY,
    FULFILL_ENQUEUE_RESULT_KEY,
    GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY,
    SEARCH_KEY,
    SEARCH_TOPIC_SCOPE_KEY,
)


def test_render_search_external_sources_is_public() -> None:
    assert callable(render_search_external_sources)


def test_search_external_sources_render_is_registered() -> None:
    pages = {page.key: page for page in build_app_pages()}

    assert pages["search_external_sources"].render is render_search_external_sources
    assert pages["search_external_sources"].title == "Search external sources"
    assert pages["search_external_sources"].url_path == "search-external-sources"
    assert pages["search_external_sources"].in_sidebar is False


def test_search_cache_matches_when_result_and_key_match() -> None:
    topic_scope_key = uuid4()
    state = {
        SEARCH_KEY: SearchExternalSourcesResult(candidates=[], source_runs=[]),
        SEARCH_TOPIC_SCOPE_KEY: str(topic_scope_key),
    }

    assert search_cache_matches(state, topic_scope_key=topic_scope_key) is True


def test_search_cache_matches_false_when_key_mismatches() -> None:
    state = {
        SEARCH_KEY: SearchExternalSourcesResult(candidates=[], source_runs=[]),
        SEARCH_TOPIC_SCOPE_KEY: str(uuid4()),
    }

    assert search_cache_matches(state, topic_scope_key=uuid4()) is False


def test_search_cache_matches_false_without_result() -> None:
    topic_scope_key = uuid4()
    state = {SEARCH_TOPIC_SCOPE_KEY: str(topic_scope_key)}

    assert search_cache_matches(state, topic_scope_key=topic_scope_key) is False


def test_search_cache_matches_false_without_topic_scope_key() -> None:
    state = {
        SEARCH_KEY: SearchExternalSourcesResult(candidates=[], source_runs=[]),
        SEARCH_TOPIC_SCOPE_KEY: str(uuid4()),
    }

    assert search_cache_matches(state, topic_scope_key=None) is False


def test_search_cache_matches_false_without_cached_topic_scope_key() -> None:
    state = {
        SEARCH_KEY: SearchExternalSourcesResult(candidates=[], source_runs=[]),
    }

    assert search_cache_matches(state, topic_scope_key=uuid4()) is False


def test_clear_downstream_ingest_caches_pops_later_step_keys() -> None:
    state = {
        SEARCH_KEY: SearchExternalSourcesResult(candidates=[], source_runs=[]),
        SEARCH_TOPIC_SCOPE_KEY: str(uuid4()),
        ARCHIVING_RESULT_KEY: object(),
        FULFILL_ENQUEUE_RESULT_KEY: object(),
        GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY: object(),
    }

    clear_downstream_ingest_caches(state)

    assert SEARCH_KEY in state
    assert SEARCH_TOPIC_SCOPE_KEY in state
    assert ARCHIVING_RESULT_KEY not in state
    assert FULFILL_ENQUEUE_RESULT_KEY not in state
    assert GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY not in state


def test_render_loads_facets_from_db_and_runs_search() -> None:
    source = inspect.getsource(render_search_external_sources)

    assert "load_topic_analysis_result" in source
    assert "search_external_sources" in source
    assert "get_topic_scope_by_key" in source
    assert "ANALYSIS_KEY" not in source
    assert "session_state.get(ANALYSIS_KEY)" not in source
    assert f'session_state["{ANALYSIS_KEY}"]' not in source
    assert f"session_state['{ANALYSIS_KEY}']" not in source
    assert f'session_state.get("{ANALYSIS_KEY}")' not in source


def test_guard_and_exit_link_targets() -> None:
    source = inspect.getsource(render_search_external_sources)

    assert "topic_analysis" in source
    assert "topic_scope" in source
    assert "paper_archiving" in source
    assert "retrieval_triage" not in source
    assert GO_TO_TOPIC_ANALYSIS_LABEL == "Go to Topic analysis"
    assert GO_TO_TOPIC_SCOPE_LABEL == "Go to Topic scope"
    assert CONTINUE_TO_PAPER_ARCHIVING_LABEL == "Continue to Paper archiving"
    assert "Topic analysis" in MISSING_PREREQUISITES_MESSAGE
