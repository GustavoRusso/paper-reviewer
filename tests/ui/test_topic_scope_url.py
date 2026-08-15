"""Topic scope id URL query helpers."""

from __future__ import annotations

from uuid import UUID

from paper_reviewer.ui.topic_scope_url import (
    TOPIC_SCOPE_PUBLIC_ID_QUERY_KEY,
    parse_topic_scope_public_id,
    topic_scope_query_params,
)


def test_parse_topic_scope_public_id_returns_uuid_when_valid() -> None:
    public_id = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    params = {TOPIC_SCOPE_PUBLIC_ID_QUERY_KEY: str(public_id)}

    assert parse_topic_scope_public_id(params) == public_id


def test_parse_topic_scope_public_id_returns_none_when_missing() -> None:
    assert parse_topic_scope_public_id({}) is None


def test_parse_topic_scope_public_id_returns_none_when_blank() -> None:
    assert parse_topic_scope_public_id({TOPIC_SCOPE_PUBLIC_ID_QUERY_KEY: ""}) is None
    assert parse_topic_scope_public_id({TOPIC_SCOPE_PUBLIC_ID_QUERY_KEY: "   "}) is None


def test_parse_topic_scope_public_id_returns_none_when_invalid() -> None:
    assert (
        parse_topic_scope_public_id({TOPIC_SCOPE_PUBLIC_ID_QUERY_KEY: "not-a-uuid"})
        is None
    )


def test_parse_topic_scope_public_id_accepts_list_value_like_streamlit() -> None:
    public_id = UUID("11111111-2222-3333-4444-555555555555")
    params = {TOPIC_SCOPE_PUBLIC_ID_QUERY_KEY: [str(public_id)]}

    assert parse_topic_scope_public_id(params) == public_id


def test_topic_scope_query_params_returns_string_dict() -> None:
    public_id = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    assert topic_scope_query_params(public_id) == {
        TOPIC_SCOPE_PUBLIC_ID_QUERY_KEY: str(public_id)
    }
