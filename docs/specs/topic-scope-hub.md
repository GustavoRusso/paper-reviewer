# Topic scope hub

This document owns the **Topic scope hub**: the Streamlit page that shows one `TopicScope` after Topic definition, then lets the user open a later phase. It is not a workflow phase step number.

Topic analysis (facets) stays in [1.2-topic-analysis.md](1.2-topic-analysis.md). Phase landings and leaf steps stay in their own specs.

For the application runtime stack (Streamlit presentation, SQLAlchemy persistence), see [technology-stack.md](../technology-stack.md).

## Glossary

| Term | Meaning |
| --- | --- |
| **Topic scope hub** | Hidden Streamlit page that shows the topic statement, stored facets, and links to the three independent later phases. Distinct from Home, Topic analysis, and phase landings. |
| **`TopicScope`** | Durable record of one topic. Product meaning: [README.md](../../README.md) Terminology. |

## Scope

### In scope (current v1)

- Dedicated Streamlit **Topic scope** page for one `TopicScope`.
- Require `topic_scope_key`. Load `TopicScope` and its facet rows from the database.
- Empty and incomplete states (missing key/row; no facet rows).
- When facets exist: topic statement, facets, then three phase `st.page_link`s. Pass `topic_scope_key` ([ui-style.md](../ui-style.md#topic-scope-key-in-the-url)).
- Home Topic scope list: each existing scope is a `st.page_link` to this hub (pass `topic_scope_key`).
- Independent phases: the user may open any later phase without completing the others. Do not add gates between those links.

### Out of scope (v1)

- NER, persist of facet rows, or auto-run of analysis ([Topic analysis](1.2-topic-analysis.md)).
- Running search external sources, paper archiving, or other ingest steps on this page.
- Listing or attaching References ([Show references](3.1-show-references.md), [Add reference](3.2-add-reference.md)).
- Topic-brief drafting ([Topic brief generation](4-topic-brief-generation.md)).
- Phase header/stepper (this page is not a phase landing or leaf step).
- A control to re-run Topic analysis.
- Cross-phase gates (a phase landing must not require the other phases to have run).

## Streamlit UI (v1)

Module: `paper_reviewer.ui.topic_scope` with `render_topic_scope()`.

Register in `paper_reviewer.ui.navigation`:

| Property | Value |
| --- | --- |
| `key` | `topic_scope` |
| `title` | Topic scope |
| `url_path` | `topic-scope` |
| `in_sidebar` | false ([ui-style.md](../ui-style.md)) |

### Page behavior (v1)

1. `st.title` **Topic scope**. Do **not** show a phase header or stepper.
2. Require `topic_scope_key`. Load `TopicScope` and its facet rows from the database (`load_topic_analysis_result`). If load fails: show an error; do not show phase links.
3. Missing key/row → empty state: *Open Topic intake to create a Topic scope, then open it here.* `st.page_link` **Go to Topic intake**. Do **not** show phase links.
4. Scope exists but **no facet rows** → incomplete state: *This Topic scope has no topic facets yet. Open Topic analysis to extract them.* `st.page_link` **Go to Topic analysis** (pass `topic_scope_key`). Do **not** show phase links.
5. When facets exist, render in this order:
   1. Caption `Reference id: \`{topic_scope_key}\``.
   2. **Topic statement** (`TopicScope.topic_statement`).
   3. **Topic facets** (same display as the analysis page: label, intent, concepts via `render_topic_facet`).
   4. Three phase **page_links** (navigate only; pass `topic_scope_key`):
      - **Continue to External sources ingestion** → `external_sources_ingestion`
      - **Continue to References selection** → `show_references` (opens [Show references](3.1-show-references.md); phase 3 has no landing)
      - **Continue to Topic brief generation** → `topic_brief_generation`
6. The user may open any phase without completing the others. Do not add gates between those links.

Phase entry contracts: [External sources ingestion](2-external-sources-ingestion.md) (landing), [References selection](3-references-selection.md) (docs-only; hub → Show references), [Topic brief generation](4-topic-brief-generation.md) (landing).

### Entry

| From | Behavior |
| --- | --- |
| **Home** | Each listed Topic scope is a `st.page_link` to **Topic scope** (`topic_scope`). The link label is the topic statement. Pass `topic_scope_key`. Keep created-at and the reference-id caption on the row. An empty list has no hub links. Owner of the Home page module: `paper_reviewer.ui.landing`. |
| **Topic analysis** | After facets exist: `st.page_link` to this hub (pass `topic_scope_key`). Do **not** `st.switch_page`. Analysis page contract: [Topic analysis](1.2-topic-analysis.md). |

## Behavior

| Case | Expected result |
| --- | --- |
| Missing key or missing `TopicScope` row | Empty state; link to Topic intake; no phase links. |
| Scope exists, no facet rows | Incomplete; link to Topic analysis; no phase links. |
| Scope exists, facet rows present | Statement, facets, three phase links; no gates. |
| Home list with one or more Topic scopes | Each row is a page_link to the hub; label is the topic statement; query has `topic_scope_key`. |

## Testability

UI slice (no Streamlit widget assertions per [tdd.md](../tdd.md)): page registered with key `topic_scope`, title **Topic scope**, url path `topic-scope`, `in_sidebar` false. View states: missing key/row → `missing_scope`; no facets → `incomplete`; facets present → `ready`. Home list hub link: page key `topic_scope`; label is the topic statement; query has `topic_scope_key`.
