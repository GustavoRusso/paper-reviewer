"""One-off live smoke test for search_external_sources → PubMed. Not a unit test."""
# Usage:
#   just sandbox-shell
#   uv run python scripts/smoke_search_external_sources.py

from __future__ import annotations

import os

from paper_reviewer.schemas.topic_brief_generation.topic_analysis import (
    TopicAnalysisResult,
)
from paper_reviewer.topic_brief_generation.search_external_sources import (
    search_external_sources,
)

analysis = TopicAnalysisResult.model_validate(
    {
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
    }
)

source_overrides = {
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
}

# Optional: export NCBI_API_KEY=... in the shell; do not hardcode the key in the file
api_key = os.environ.get("NCBI_API_KEY") or None
result = search_external_sources(
    analysis,
    source_overrides=source_overrides,
    api_key=api_key,
)

print("source_runs:", [r.model_dump() for r in result.source_runs])
print("candidate_count:", len(result.candidates))
for c in result.candidates[:5]:
    print(f"- {c.source_uid}: {c.title!r} ({c.published_year}) doi={c.doi}")
