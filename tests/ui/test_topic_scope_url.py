"""Generation id URL query helpers."""

from __future__ import annotations

from uuid import UUID

from paper_reviewer.ui.generation_url import (
    GENERATION_PUBLIC_ID_QUERY_KEY,
    generation_query_params,
    parse_generation_public_id,
)


def test_parse_generation_public_id_returns_uuid_when_valid() -> None:
    public_id = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    params = {GENERATION_PUBLIC_ID_QUERY_KEY: str(public_id)}

    assert parse_generation_public_id(params) == public_id


def test_parse_generation_public_id_returns_none_when_missing() -> None:
    assert parse_generation_public_id({}) is None


def test_parse_generation_public_id_returns_none_when_blank() -> None:
    assert parse_generation_public_id({GENERATION_PUBLIC_ID_QUERY_KEY: ""}) is None
    assert parse_generation_public_id({GENERATION_PUBLIC_ID_QUERY_KEY: "   "}) is None


def test_parse_generation_public_id_returns_none_when_invalid() -> None:
    assert (
        parse_generation_public_id({GENERATION_PUBLIC_ID_QUERY_KEY: "not-a-uuid"})
        is None
    )


def test_parse_generation_public_id_accepts_list_value_like_streamlit() -> None:
    public_id = UUID("11111111-2222-3333-4444-555555555555")
    params = {GENERATION_PUBLIC_ID_QUERY_KEY: [str(public_id)]}

    assert parse_generation_public_id(params) == public_id


def test_generation_query_params_returns_string_dict() -> None:
    public_id = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    assert generation_query_params(public_id) == {
        GENERATION_PUBLIC_ID_QUERY_KEY: str(public_id)
    }
