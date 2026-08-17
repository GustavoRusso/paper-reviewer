"""Topic scope key in Streamlit URL query parameters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

import streamlit as st

from paper_reviewer.ui.navigation import streamlit_page_for

TOPIC_SCOPE_KEY_QUERY_KEY = "topic_scope_key"
DOI_QUERY_KEY = "doi"


def parse_topic_scope_key(query_params: Mapping[str, Any]) -> UUID | None:
    """Return the Topic scope key from URL query params, or None."""
    raw = query_params.get(TOPIC_SCOPE_KEY_QUERY_KEY)
    if raw is None:
        return None
    if isinstance(raw, (list, tuple)):
        if not raw:
            return None
        raw = raw[0]
    text = str(raw).strip()
    if not text:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


def parse_doi(query_params: Mapping[str, Any]) -> str | None:
    """Return an uppercase DOI from URL query params, or None."""
    raw = query_params.get(DOI_QUERY_KEY)
    if raw is None:
        return None
    if isinstance(raw, (list, tuple)):
        if not raw:
            return None
        raw = raw[0]
    text = str(raw).strip()
    if not text:
        return None
    return text.upper()


def topic_scope_query_params(topic_scope_key: UUID) -> dict[str, str]:
    """Build query params that keep the Topic scope key across page navigation."""
    return {TOPIC_SCOPE_KEY_QUERY_KEY: str(topic_scope_key)}


def workflow_switch_page(page_key: str, *, topic_scope_key: UUID) -> None:
    """Switch to a workflow page and keep the Topic scope key in the URL.

    Streamlit clears query params when ``query_params`` is omitted. Always pass
    the key so the destination URL does not lose it.
    """
    st.switch_page(
        streamlit_page_for(page_key),
        query_params=topic_scope_query_params(topic_scope_key),
    )


def workflow_page_link(
    page_key: str,
    *,
    label: str,
    topic_scope_key: UUID | None,
    extra_query: Mapping[str, str] | None = None,
) -> None:
    """Link to a workflow page and preserve the Topic scope key when present.

    Streamlit clears query params when ``query_params`` is omitted. Always pass
    the key for in-workflow navigation so the URL does not lose it. Extra query
    fields (for example ``doi``) merge with that key.
    """
    kwargs: dict[str, Any] = {
        "label": label,
    }
    query: dict[str, str] = {}
    if topic_scope_key is not None:
        query.update(topic_scope_query_params(topic_scope_key))
    if extra_query:
        query.update(extra_query)
    if query:
        kwargs["query_params"] = query
    st.page_link(streamlit_page_for(page_key), **kwargs)
