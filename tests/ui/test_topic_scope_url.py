"""Topic scope key URL query helpers."""

from __future__ import annotations

from uuid import UUID

import pytest

from paper_reviewer.ui.topic_scope_url import (
    DOI_QUERY_KEY,
    TOPIC_SCOPE_KEY_QUERY_KEY,
    parse_doi,
    parse_topic_scope_key,
    topic_scope_query_params,
    workflow_page_link,
    workflow_switch_page,
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


def test_workflow_switch_page_passes_topic_scope_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    fake_page = object()

    def fake_page_for(key: str) -> object:
        captured["page_key"] = key
        return fake_page

    def fake_switch_page(page: object, **kwargs: object) -> None:
        captured["page"] = page
        captured["kwargs"] = kwargs

    monkeypatch.setattr(
        "paper_reviewer.ui.topic_scope_url.streamlit_page_for",
        fake_page_for,
    )
    monkeypatch.setattr(
        "paper_reviewer.ui.topic_scope_url.st.switch_page",
        fake_switch_page,
    )

    topic_scope_key = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    workflow_switch_page("topic_analysis", topic_scope_key=topic_scope_key)

    assert captured["page_key"] == "topic_analysis"
    assert captured["page"] is fake_page
    assert captured["kwargs"] == {
        "query_params": {TOPIC_SCOPE_KEY_QUERY_KEY: str(topic_scope_key)}
    }


def test_parse_doi_strips_and_uppercases() -> None:
    assert parse_doi({DOI_QUERY_KEY: " 10.1000/example "}) == "10.1000/EXAMPLE"


def test_parse_doi_returns_none_when_missing_or_blank() -> None:
    assert parse_doi({}) is None
    assert parse_doi({DOI_QUERY_KEY: ""}) is None
    assert parse_doi({DOI_QUERY_KEY: "   "}) is None


def test_parse_doi_accepts_list_value_like_streamlit() -> None:
    assert parse_doi({DOI_QUERY_KEY: ["10.1000/a"]}) == "10.1000/A"


def test_workflow_page_link_passes_topic_scope_key_and_extra_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    fake_page = object()

    def fake_page_for(key: str) -> object:
        captured["page_key"] = key
        return fake_page

    def fake_page_link(page: object, **kwargs: object) -> None:
        captured["page"] = page
        captured["kwargs"] = kwargs

    monkeypatch.setattr(
        "paper_reviewer.ui.topic_scope_url.streamlit_page_for",
        fake_page_for,
    )
    monkeypatch.setattr(
        "paper_reviewer.ui.topic_scope_url.st.page_link",
        fake_page_link,
    )

    topic_scope_key = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    workflow_page_link(
        "paper_brief",
        label="Read paper brief",
        topic_scope_key=topic_scope_key,
        extra_query={DOI_QUERY_KEY: "10.1000/EXAMPLE"},
    )

    assert captured["page_key"] == "paper_brief"
    assert captured["page"] is fake_page
    assert captured["kwargs"] == {
        "label": "Read paper brief",
        "query_params": {
            TOPIC_SCOPE_KEY_QUERY_KEY: str(topic_scope_key),
            DOI_QUERY_KEY: "10.1000/EXAMPLE",
        },
    }
