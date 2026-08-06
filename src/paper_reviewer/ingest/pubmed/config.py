"""Build dlt RESTAPIConfig for PubMed ESearch → ESummary (History)."""

from __future__ import annotations

import json
from typing import Any

from dlt.sources.rest_api.typing import RESTAPIConfig

EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
# NCBI JSON ESummary rejects requests larger than this.
ESUMMARY_JSON_RETMAX_CAP = 500
# Used when caller omits retmax so History mode never fetches the full set.
ESUMMARY_DEFAULT_RETMAX = 20


def build_pubmed_rest_api_config(
    *,
    term: str,
    retmax: int | None = None,
    sort: str | None = None,
    api_key: str | None = None,
) -> RESTAPIConfig:
    """Declarative ESearch + ESummary config linked via History WebEnv/query_key."""
    esearch_params: dict[str, Any] = {
        "db": "pubmed",
        "retmode": "json",
        "usehistory": "y",
        "term": term,
    }
    if retmax is not None:
        esearch_params["retmax"] = retmax
    if sort is not None:
        esearch_params["sort"] = sort

    # History stores the full hit set; ESummary must pass retmax or NCBI tries
    # to return every UID (JSON max 500).
    esummary_retmax = (
        ESUMMARY_DEFAULT_RETMAX
        if retmax is None
        else min(retmax, ESUMMARY_JSON_RETMAX_CAP)
    )

    client: dict[str, Any] = {"base_url": EUTILS_BASE_URL}
    if api_key is not None:
        client["auth"] = {
            "type": "api_key",
            "name": "api_key",
            "api_key": api_key,
            "location": "query",
        }

    return {
        "client": client,
        "resources": [
            {
                "name": "esearch",
                "endpoint": {
                    "path": "esearch.fcgi",
                    "params": esearch_params,
                    "data_selector": "esearchresult",
                    "paginator": "single_page",
                },
            },
            {
                "name": "esummary",
                "endpoint": {
                    "path": "esummary.fcgi",
                    "params": {
                        "db": "pubmed",
                        "retmode": "json",
                        "retmax": esummary_retmax,
                        "WebEnv": "{resources.esearch.webenv}",
                        "query_key": "{resources.esearch.querykey}",
                    },
                    "paginator": "single_page",
                    "response_actions": [_flatten_esummary_docsums],
                    "data_selector": "docsums",
                },
            },
        ],
    }


def _flatten_esummary_docsums(response: Any, *args: Any, **kwargs: Any) -> Any:
    """Rewrite ESummary JSON so DocSums are a list under ``docsums``."""
    payload = response.json()
    error = payload.get("error")
    if error:
        raise RuntimeError(str(error))
    result = payload.get("result") or {}
    uids = result.get("uids") or []
    records = [result[uid] for uid in uids if isinstance(result.get(uid), dict)]
    response._content = json.dumps({"docsums": records}).encode("utf-8")
    response.encoding = "utf-8"
    return response
