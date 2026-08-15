# Paper search (phase landing)

This document is the specification for the **Paper search** phase landing in [README.md](../../README.md). v1 is a **shell**. Local-database search is not built yet.

**Independent phases:** the user may open this landing without running External sources ingestion or Topic brief. Do not add cross-phase gates in v1.

## Glossary

| Term | Meaning |
| --- | --- |
| **Paper search** | Phase 3: search only papers already ingested in the local database, then confirm which papers continue to Topic brief. |
| **Phase landing** | Hidden Streamlit page reached from the [Topic scope hub](1.2-topic-analysis.md#topic-scope-hub). |

## Scope

### In scope (current v1)

- Dedicated landing page with title **Paper search**.
- Caption that local Paper search is not built yet.
- Page_link back to **Topic scope** (pass `topic_scope_key`).

### Out of scope (v1)

- Querying the local paper index.
- A confirm gate for which local papers continue to Topic brief (planned with this phase; not built yet).
- Confirmed-paper attachment tables on `TopicScope`.

## Streamlit UI (v1)

Module: `paper_reviewer.ui.paper_search` with `render_paper_search()`.

| Property | Value |
| --- | --- |
| `key` | `paper_search` |
| `title` | Paper search |
| `url_path` | `paper-search` |
| `in_sidebar` | false ([ui-style.md](../ui-style.md)) |

### Page behavior

1. Require `topic_scope_key`. Missing key → empty state + page_link to **Topic intake** and **Topic scope**.
2. Show title **Paper search** and a caption that search of locally ingested papers is not built yet.
3. Page_link to **Topic scope**.

Entry from the hub: [Topic analysis](1.2-topic-analysis.md#topic-scope-hub).
