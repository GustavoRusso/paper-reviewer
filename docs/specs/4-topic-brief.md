# Topic brief (phase landing)

This document is the specification for the **Topic brief** phase landing in [README.md](../../README.md). v1 is a **shell**. Cited topic-brief drafting is not built yet.

**Independent phases:** the user may open this landing without running Paper ingestion or Paper search. Do not add cross-phase gates in v1.

## Glossary

| Term | Meaning |
| --- | --- |
| **Topic brief** | Phase 4 result: a cited introduction that explains what is currently known about the topic, attached to the `TopicScope`. Distinct from a **paper brief**. |
| **Phase landing** | Hidden Streamlit page reached from the [Topic scope hub](1.2-topic-analysis.md#topic-scope-hub). |

## Scope

### In scope (current v1)

- Dedicated landing page with title **Topic brief**.
- Caption that Topic brief drafting is not built yet.
- Page_link back to **Topic scope** (pass `topic_scope_public_id`).

### Out of scope (v1)

- LLM drafting of the cited topic brief.
- Citation scoping to claims.
- Attaching a topic-brief artifact to `TopicScope`.
- Generate paper brief (ingest step) — [07-generate-paper-brief.md](07-generate-paper-brief.md).

## Streamlit UI (v1)

Module: `paper_reviewer.ui.topic_brief` with `render_topic_brief()`.

| Property | Value |
| --- | --- |
| `key` | `topic_brief` |
| `title` | Topic brief |
| `url_path` | `topic-brief` |
| `in_sidebar` | false ([ui-style.md](../ui-style.md)) |

### Page behavior

1. Require `topic_scope_public_id`. Missing id → empty state + page_link to **Topic intake** and **Topic scope**.
2. Show title **Topic brief** and a caption that drafting the cited topic brief is not built yet.
3. Page_link to **Topic scope**.

Entry from the hub: [Topic analysis](1.2-topic-analysis.md#topic-scope-hub).
