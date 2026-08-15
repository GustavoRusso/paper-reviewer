# Paper ingestion (phase landing)

This document is the specification for the **Paper ingestion** phase landing in [README.md](../../README.md). It is a short UI shell. Step behavior for ingest stays in the existing step specs.

**Independent phases:** the user may open this landing without running Paper search or Topic brief. Do not add cross-phase gates in v1.

## Glossary

| Term | Meaning |
| --- | --- |
| **Paper ingestion** | Phase 2: discover papers from paper sources, archive them, fill metadata, generate paper briefs, and (later) index them. |
| **Phase landing** | Hidden Streamlit page reached from the [Topic scope hub](1.2-topic-analysis.md#topic-scope-hub). |

## Scope

### In scope (current v1)

- Dedicated landing page for Paper ingestion on the current `TopicScope`.
- Short intro for this phase.
- Primary `st.page_link` to **Related-paper search** (first existing ingest step).
- Optional `st.page_link`s to later ingest pages that already exist (Paper archiving, Fulfill papers metadata, Generate paper brief) without requiring the user to have finished earlier ingest steps.
- Pass `topic_scope_public_id` on every in-workflow link ([ui-style.md](../ui-style.md#topic-scope-public-id-in-the-url)).

### Out of scope

- Running related-paper search, archiving, EFetch, or brief jobs on this landing.
- Paper indexing (still later).
- Local Paper search or topic-brief drafting.

## Streamlit UI (v1)

Module: `paper_reviewer.ui.paper_ingestion` with `render_paper_ingestion()`.

| Property | Value |
| --- | --- |
| `key` | `paper_ingestion` |
| `title` | Paper ingestion |
| `url_path` | `paper-ingestion` |
| `in_sidebar` | false ([ui-style.md](../ui-style.md)) |

### Page behavior

1. Require `topic_scope_public_id`. Missing id → empty state + page_link to **Topic intake** and **Topic scope**.
2. Show a short intro: this phase searches paper sources and ingests papers for this Topic scope.
3. Primary next: page_link **Continue to Related-paper search** (`related_paper_search`). Do **not** auto-run search here. Do **not** `switch_page`.
4. Optional further links (same query id): **Paper archiving**, **Fulfill papers metadata**, **Generate paper brief**. Those pages keep their own prerequisite guards.

Entry from the hub: [Topic analysis](1.2-topic-analysis.md#topic-scope-hub). First ingest step: [related-paper search](03-related-paper-search.md).

## Step specs (do not copy)

| Step | Spec |
| --- | --- |
| Related-paper search | [03-related-paper-search.md](03-related-paper-search.md) |
| Paper archiving | [05-paper-archiving.md](05-paper-archiving.md) |
| Fulfill papers metadata | [06-fulfill-papers-metadata.md](06-fulfill-papers-metadata.md) |
| Generate paper brief | [07-generate-paper-brief.md](07-generate-paper-brief.md) |
| Paper indexing | Later |

Retrieval triage today still follows related-paper search inside this ingest chain — [04-retrieval-triage.md](04-retrieval-triage.md). Local Paper search as a separate phase is [3-paper-search.md](3-paper-search.md).
