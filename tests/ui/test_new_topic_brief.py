"""New Topic brief: reset session on successful Submit."""

from __future__ import annotations

from uuid import UUID

from paper_reviewer.schemas.topic_brief_generation.topic_intake import TopicStatement
from paper_reviewer.ui.new_topic_brief import (
    ARCHIVING_RESULT_KEY,
    FULFILL_ENQUEUE_RESULT_KEY,
    GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY,
    SESSION_KEY,
    TRIAGE_RESULT_KEY,
    begin_new_topic_brief_session,
)


def test_begin_new_topic_brief_session_clears_leftover_and_unknown_keys() -> None:
    topic = TopicStatement(text="Gaucher disease enzyme replacement")
    state = {
        SESSION_KEY: TopicStatement(text="previous topic"),
        TRIAGE_RESULT_KEY: "stale-triage",
        ARCHIVING_RESULT_KEY: "stale-archiving",
        FULFILL_ENQUEUE_RESULT_KEY: "stale-fulfill",
        GENERATE_PAPER_BRIEF_ENQUEUE_RESULT_KEY: "stale-brief",
        "unknown_leftover_key": "must-go",
        "topic_brief_generation_public_id": UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
    }

    begin_new_topic_brief_session(state, topic_statement=topic)

    assert set(state) == {SESSION_KEY}
    assert state[SESSION_KEY] is topic


def test_begin_new_topic_brief_session_from_empty_state() -> None:
    topic = TopicStatement(text="lysosomal storage disorders")
    state: dict[str, object] = {}

    begin_new_topic_brief_session(state, topic_statement=topic)

    assert set(state) == {SESSION_KEY}
    assert state[SESSION_KEY] is topic
