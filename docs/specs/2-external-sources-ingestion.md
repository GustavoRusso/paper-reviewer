# External sources ingestion (phase landing)

This document is the specification for the **External sources ingestion** phase landing in [README.md](../../README.md). It is a short UI shell. Step behavior for ingest stays in the existing step specs.

**Independent phases:** the user may open this landing without running References selection or Topic brief generation. Do not add cross-phase gates in v1.

## Glossary

| Term | Meaning |
| --- | --- |
| **External sources ingestion** | Phase 2: search external sources, then run **Paper Ingestion** (archive, fulfill metadata, generate paper briefs, and index). |
| **Paper Ingestion** | Docs-only step group 2.2 under this phase. Index: [2.2-external-sources-ingestion.md](2.2-external-sources-ingestion.md). |
| **Phase landing** | Hidden Streamlit page reached from the [Topic scope hub](1.2-topic-analysis.md#topic-scope-hub). |

## Scope

### In scope (current v1)

- Dedicated landing page for External sources ingestion on the current `TopicScope`.
- Shared phase header (phase title, Reference id caption when the key is present, intro, progress stepper) on the landing and on every leaf ingest step page.
- Primary `st.page_link` on the landing to **Search external sources** (first existing ingest step).
- Pass `topic_scope_key` on every in-workflow link ([ui-style.md](../ui-style.md#topic-scope-key-in-the-url)).

### Out of scope

- Running search external sources, archiving, EFetch, or brief jobs on this landing.
- A Streamlit page for the 2.2 Paper Ingestion group ([2.2-external-sources-ingestion.md](2.2-external-sources-ingestion.md)).
- Paper indexing page (still later — [2.2.4-paper-indexing.md](2.2.4-paper-indexing.md)).
- References selection or topic-brief drafting.

## Streamlit UI (v1)

Module: `paper_reviewer.ui.external_sources_ingestion` with `render_external_sources_ingestion()` (landing) and `render_external_sources_ingestion_header()` (shared chrome).

| Property | Value |
| --- | --- |
| `key` | `external_sources_ingestion` |
| `title` | External sources ingestion |
| `url_path` | `external-sources-ingestion` |
| `in_sidebar` | false ([ui-style.md](../ui-style.md)) |

### Phase header (landing and ingest steps)

Call `render_external_sources_ingestion_header` on the landing when a Topic scope key is present (the phase title lives in the header), and before the step name on every External sources ingestion leaf step page. Step pages show the step name with `st.header` after the header. Do **not** copy this chrome into other phases.

| Part | Behavior |
| --- | --- |
| Phase title | `st.title` **External sources ingestion** (`PHASE_TITLE`). |
| Reference id | When `topic_scope_key` is present: caption `Reference id: \`{topic_scope_key}\``. |
| Intro | Short phase description: this phase searches external sources and ingests papers for this Topic scope. |
| Stepper | One control per **leaf** ingest step, in order. Other steps are `st.page_link`s (destination labels; pass `topic_scope_key`). The current step is **not** a link: bold label plus a **Current** badge. Do **not** show the 2.2 group as its own stepper entry. |
| Landing | No step is current. The stepper still lists every leaf ingest step so the user can open a later page without finishing earlier ones. Those pages keep their own prerequisite guards. |
| Missing key | Landing empty state only. Show the phase title (`st.title`); do **not** render the full header (no intro/stepper). |

v1 stepper steps (Paper indexing later): Search external sources, Paper archiving, Fulfill papers metadata, Generate paper brief.

Control mapping: [ui-style.md](../ui-style.md#phase-chrome).

### Page behavior

1. Require `topic_scope_key`. Missing key → phase title + empty state + page_link to **Topic intake** and **Topic scope**.
2. Show the phase header (phase title, Reference id caption, intro, stepper).
3. Primary next: page_link **Continue to Search external sources** (`search_external_sources`). Do **not** auto-run search here. Do **not** `switch_page`.

Entry from the hub: [Topic analysis](1.2-topic-analysis.md#topic-scope-hub). First ingest step: [search external sources](2.1-search-external-sources.md) (phase 2 step 1).

## Step specs (do not copy)

| Step | Spec |
| --- | --- |
| Search external sources (2.1) | [2.1-search-external-sources.md](2.1-search-external-sources.md) |
| Paper Ingestion (2.2, group) | [2.2-external-sources-ingestion.md](2.2-external-sources-ingestion.md) |
| Paper archiving (2.2.1) | [2.2.1-paper-archiving.md](2.2.1-paper-archiving.md) |
| Fulfill papers metadata (2.2.2) | [2.2.2-fulfill-papers-metadata.md](2.2.2-fulfill-papers-metadata.md) |
| Generate paper brief (2.2.3) | [2.2.3-generate-paper-brief.md](2.2.3-generate-paper-brief.md) |
| Paper indexing (2.2.4) | [2.2.4-paper-indexing.md](2.2.4-paper-indexing.md) |

References selection as a separate phase is [3-references-selection.md](3-references-selection.md) (docs-only overview; hub opens Show references).
