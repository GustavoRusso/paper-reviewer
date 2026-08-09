"""One-off live smoke test for search_related_papers → PubMed. Not a unit test."""
# Usage:
#   just sandbox-shell
#   uv run python scripts/smoke_search_related_papers.py

from __future__ import annotations

import os

from paper_reviewer.schemas.search import SearchCriteria
from paper_reviewer.search import search_related_papers

criteria = SearchCriteria.model_validate(
    {
        "topic_analysis": {
            "facets": [
                {
                    "id": "core-concepts",
                    "label": "Core concepts",
                    "intent": "Narrow topical match",
                    "concepts": ["glioblastoma", "immunotherapy"],
                    "synonyms": ["GBM"],
                    "date_from": "2018-01-01",
                    "date_to": None,
                    "filters": {},
                    "retmax": 5,
                }
            ]
        },
        "source_overrides": {
            "pubmed": {
                "facets": {
                    "core-concepts": {
                        "raw_term": (
                            "glioblastoma[mesh] AND immunotherapy[Title/Abstract] "
                            "AND 2018:3000[pdat]"
                        ),
                        "retmax": 5,
                    }
                }
            }
        },
    }
)

# Optional: export NCBI_API_KEY=... in the shell; do not hardcode the key in the file
api_key = os.environ.get("NCBI_API_KEY") or None
result = search_related_papers(criteria, api_key=api_key)

print("source_runs:", [r.model_dump() for r in result.source_runs])
print("candidate_count:", len(result.candidates))
for c in result.candidates[:5]:
    print(f"- {c.source_uid}: {c.title!r} ({c.published_year}) doi={c.doi}")
