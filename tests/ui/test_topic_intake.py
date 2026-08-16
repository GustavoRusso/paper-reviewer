"""Topic intake: reset session on successful Submit."""

from __future__ import annotations

import inspect
from uuid import UUID

from paper_reviewer.schemas.topic_scope.topic_intake import TopicStatement
from paper_reviewer.ui.topic_intake import (
    ARCHIVING_RESULT_KEY,
    FULFILL_ENQUEUE_RESULT_KEY,
    GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY,
    SEARCH_KEY,
    SESSION_KEY,
    begin_topic_intake_session,
    render_topic_intake,
)


def test_begin_topic_intake_session_clears_leftover_and_unknown_keys() -> None:
    topic = TopicStatement(text="Gaucher disease enzyme replacement")
    state = {
        SESSION_KEY: TopicStatement(text="previous topic"),
        SEARCH_KEY: "stale-search",
        ARCHIVING_RESULT_KEY: "stale-archiving",
        FULFILL_ENQUEUE_RESULT_KEY: "stale-fulfill",
        GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY: "stale-brief",
        "unknown_leftover_key": "must-go",
        "leftover_session_key": UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
    }

    begin_topic_intake_session(state, topic_statement=topic)

    assert set(state) == {SESSION_KEY}
    assert state[SESSION_KEY] is topic


def test_begin_topic_intake_session_from_empty_state() -> None:
    topic = TopicStatement(text="lysosomal storage disorders")
    state: dict[str, object] = {}

    begin_topic_intake_session(state, topic_statement=topic)

    assert set(state) == {SESSION_KEY}
    assert state[SESSION_KEY] is topic


def test_topic_intake_switches_to_analysis_with_topic_scope_key() -> None:
    source = inspect.getsource(render_topic_intake)
    assert "workflow_switch_page" in source
    assert "st.switch_page" not in source
