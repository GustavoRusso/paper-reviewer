"""Topic scope key URL query helpers."""

from __future__ import annotations

from uuid import UUID

from paper_reviewer.ui.topic_scope_url import (
    TOPIC_SCOPE_KEY_QUERY_KEY,
    parse_topic_scope_key,
    topic_scope_query_params,
)


def test_parse_topic_scope_key_returns_uuid_when_valid() -> None:
    topic_scope_key = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    params = {TOPIC_SCOPE_KEY_QUERY_KEY: str(topic_scope_key)}

    assert parse_topic_scope_key(params) == topic_scope_key


def test_parse_topic_scope_key_returns_none_when_missing() -> None:
    assert parse_topic_scope_key({}) is None


def test_parse_topic_scope_key_returns_none_when_blank() -> None:
    assert parse_topic_scope_key({TOPIC_SCOPE_KEY_QUERY_KEY: ""}) is None
    assert parse_topic_scope_key({TOPIC_SCOPE_KEY_QUERY_KEY: "   "}) is None


def test_parse_topic_scope_key_returns_none_when_invalid() -> None:
    assert parse_topic_scope_key({TOPIC_SCOPE_KEY_QUERY_KEY: "not-a-uuid"}) is None


def test_parse_topic_scope_key_accepts_list_value_like_streamlit() -> None:
    topic_scope_key = UUID("11111111-2222-3333-4444-555555555555")
    params = {TOPIC_SCOPE_KEY_QUERY_KEY: [str(topic_scope_key)]}

    assert parse_topic_scope_key(params) == topic_scope_key


def test_topic_scope_query_params_returns_string_dict() -> None:
    topic_scope_key = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    assert topic_scope_query_params(topic_scope_key) == {
        TOPIC_SCOPE_KEY_QUERY_KEY: str(topic_scope_key)
    }
