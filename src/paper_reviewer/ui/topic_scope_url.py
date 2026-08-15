"""Topic brief generation public id in Streamlit URL query parameters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

import streamlit as st

from paper_reviewer.ui.navigation import streamlit_page_for

GENERATION_PUBLIC_ID_QUERY_KEY = "topic_brief_generation_public_id"


def parse_generation_public_id(query_params: Mapping[str, Any]) -> UUID | None:
    """Return the generation public id from URL query params, or None."""
    raw = query_params.get(GENERATION_PUBLIC_ID_QUERY_KEY)
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


def generation_query_params(public_id: UUID) -> dict[str, str]:
    """Build query params that keep the generation id across page navigation."""
    return {GENERATION_PUBLIC_ID_QUERY_KEY: str(public_id)}


def set_generation_public_id_in_url(public_id: UUID) -> None:
    """Write the generation public id into the current page URL."""
    st.query_params[GENERATION_PUBLIC_ID_QUERY_KEY] = str(public_id)


def workflow_page_link(
    page_key: str,
    *,
    label: str,
    public_id: UUID | None,
) -> None:
    """Link to a workflow page and preserve the generation id when present.

    Streamlit clears query params when ``query_params`` is omitted. Always pass
    the id for in-workflow navigation so the URL does not lose it.
    """
    kwargs: dict[str, Any] = {
        "label": label,
    }
    if public_id is not None:
        kwargs["query_params"] = generation_query_params(public_id)
    st.page_link(streamlit_page_for(page_key), **kwargs)
