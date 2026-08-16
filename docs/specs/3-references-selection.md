# References selection (phase overview)

This document is the specification for the **References selection** phase in [README.md](../../README.md). It is **docs-only** in v1: there is no dedicated Streamlit landing page. The Topic scope hub opens the first leaf step, [Show references](3.1-show-references.md).

Step behavior stays in the step specs. Local **Papers search** and Reference attach (**Add** / **Add all**) are built.

**Independent phases:** the user may open Show references without running External sources ingestion or Topic brief generation. Do not add cross-phase gates in v1.

## Glossary

| Term | Meaning |
| --- | --- |
| **References selection** | Phase 3: select ingested `Paper`s as **References** for the current `TopicScope` (inputs for Topic brief). |
| **Reference** | Durable many-to-many link from one `TopicScope` to one ingested `Paper`. Distinct from a **bibliographic reference** (paper→paper citation) and from the UI caption **Reference id** (`topic_scope_key`). |

## Scope

### In scope (this document)

- Name the phase and point to leaf specs.
- Own the shared phase header and stepper chrome used on every References selection leaf step page.
- State that v1 has no phase landing page; hub entry is Show references.

### Out of scope

- Listing References or attaching papers (owned by [3.1](3.1-show-references.md) and [3.2](3.2-add-reference.md)).
- Running [Papers search](papers-search.md) on phase chrome.
- Topic brief generation ([4-topic-brief-generation.md](4-topic-brief-generation.md)).

## Streamlit chrome (v1)

Module: `paper_reviewer.ui.references_selection` with `render_references_selection_header()` (shared chrome only). No registered `AppPage` for a phase landing.

Call `render_references_selection_header` before the step name on every References selection leaf step page. Step pages show the step name with `st.header` after the header. Do **not** copy this chrome into other phases.

| Part | Behavior |
| --- | --- |
| Phase title | `st.title` **References selection** (`PHASE_TITLE`). |
| Reference id | When `topic_scope_key` is present: caption `Reference id: \`{topic_scope_key}\``. |
| Intro | Short phase description: this phase selects ingested papers as References for this Topic scope. |
| Stepper | One control per leaf step, in order: Show references, Add reference. Other steps are `st.page_link`s (destination labels; pass `topic_scope_key`). The current step is **not** a link: bold label plus a **Current** badge. |

Control mapping: [ui-style.md](../ui-style.md#phase-chrome).

Entry from the hub: [Topic analysis](1.2-topic-analysis.md#topic-scope-hub) → **Show references** (pass `topic_scope_key`). First step: [Show references](3.1-show-references.md).

## Step specs (do not copy)

| Step | Spec | Streamlit page (v1) |
| --- | --- | --- |
| Show references (3.1) | [3.1-show-references.md](3.1-show-references.md) | Yes (hub entry) |
| Add reference (3.2) | [3.2-add-reference.md](3.2-add-reference.md) | Yes |

Shared local search capability used by Add reference: [Papers search](papers-search.md).
