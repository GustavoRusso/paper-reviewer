# References selection (phase landing)

This document is the specification for the **References selection** phase landing in [README.md](../../README.md). Step behavior stays in the step specs. Local **Papers search** and per-paper **Add** are built; **Add all** is not built yet.

**Independent phases:** the user may open this landing without running External sources ingestion or Topic brief. Do not add cross-phase gates in v1.

## Glossary

| Term | Meaning |
| --- | --- |
| **References selection** | Phase 3: select ingested `Paper`s as **References** for the current `TopicScope` (inputs for Topic brief). |
| **Reference** | Durable many-to-many link from one `TopicScope` to one ingested `Paper`. Distinct from a **bibliographic reference** (paper→paper citation) and from the UI caption **Reference id** (`topic_scope_key`). |
| **Phase landing** | Hidden Streamlit page reached from the [Topic scope hub](1.2-topic-analysis.md#topic-scope-hub). |

## Scope

### In scope (current v1)

- Dedicated landing page for References selection on the current `TopicScope`.
- Shared phase header (phase title, Reference id caption when the key is present, intro, progress stepper) on the landing and on every leaf step page.
- Primary `st.page_link` on the landing to **Show references** (step 3.1).
- Pass `topic_scope_key` on every in-workflow link ([ui-style.md](../ui-style.md#topic-scope-key-in-the-url)).

### Out of scope

- Listing References or attaching papers on this landing (owned by [3.1](3.1-show-references.md) and [3.2](3.2-add-reference.md)).
- Running [Papers search](papers-search.md) on this landing.
- Topic-brief drafting ([4-topic-brief.md](4-topic-brief.md)).

## Streamlit UI (v1)

Module: `paper_reviewer.ui.references_selection` with `render_references_selection()` (landing) and `render_references_selection_header()` (shared chrome).

| Property | Value |
| --- | --- |
| `key` | `references_selection` |
| `title` | References selection |
| `url_path` | `references-selection` |
| `in_sidebar` | false ([ui-style.md](../ui-style.md)) |

### Phase header (landing and leaf steps)

Call `render_references_selection_header` on the landing when a Topic scope key is present (the phase title lives in the header), and before the step name on every References selection leaf step page. Step pages show the step name with `st.header` after the header. Do **not** copy this chrome into other phases.

| Part | Behavior |
| --- | --- |
| Phase title | `st.title` **References selection** (`PHASE_TITLE`). |
| Reference id | When `topic_scope_key` is present: caption `Reference id: \`{topic_scope_key}\``. |
| Intro | Short phase description: this phase selects ingested papers as References for this Topic scope. |
| Stepper | One control per leaf step, in order: Show references, Add reference. Other steps are `st.page_link`s (destination labels; pass `topic_scope_key`). The current step is **not** a link: bold label plus a **Current** badge. |
| Landing | No step is current. The stepper still lists every leaf step so the user can open a later page without finishing earlier ones. Those pages keep their own prerequisite guards. |
| Missing key | Landing empty state only. Show the phase title (`st.title`); do **not** render the full header (no intro/stepper). |

Control mapping: [ui-style.md](../ui-style.md#phase-chrome).

### Page behavior

1. Require `topic_scope_key`. Missing key → phase title + empty state + page_link to **Topic intake** and **Topic scope**.
2. Show the phase header (phase title, Reference id caption, intro, stepper).
3. Primary next: page_link **Continue to Show references** (`show_references`). Do **not** auto-run search or attach here. Do **not** `switch_page`.

Entry from the hub: [Topic analysis](1.2-topic-analysis.md#topic-scope-hub). First step: [Show references](3.1-show-references.md) (phase 3 step 1).

## Step specs (do not copy)

| Step | Spec |
| --- | --- |
| Show references (3.1) | [3.1-show-references.md](3.1-show-references.md) |
| Add reference (3.2) | [3.2-add-reference.md](3.2-add-reference.md) |

Shared local search capability used by Add reference: [Papers search](papers-search.md).
