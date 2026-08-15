# Development practices

Shared repository practices for contributors and coding agents. Add new sections here as more practices land.

## File moves and renames

For any **tracked** file or directory move/rename, use host `git mv`:

```bash
git mv src/paper_reviewer/old_name.py src/paper_reviewer/new_name.py
```

- Agents must use the Shell tool for that. Do **not** use filesystem-only moves (`mv` / `Move-Item` / `ren`) or Delete + Write: those look like delete + add and weaken rename tracking.
- After `git mv`, update imports and other references in a separate edit step.
- Untracked or new files may use a normal filesystem move; then `git add` the new path if they should be tracked.
- If a tool already created a delete+add pair for a tracked rename, fix it with `git add -A` on both paths (or re-do with `git mv`) before commit so `git status` shows rename when similarity allows.

## Identifier naming (`id` vs `key`)

This section owns how code, database columns, and URLs name identifiers. It does **not** own URL query behavior ([ui-style.md](ui-style.md)) or which fields an entity has (the step spec).

When a persisted entity has a surrogate primary key **and** a value that the user or a URL may see:

| Name | Role | Where it appears |
| --- | --- | --- |
| `id` | Private surrogate primary key | ORM attribute, Postgres column, and FKs only. Never in URLs, query parameters, public helpers, or captions. |
| `key` | Minted user-facing identifier (UUID we assign) | ORM attribute, Postgres column, URL query `{entity}_key`, and lookup helpers `get_<entity>_by_key`. |
| Domain name (`doi`, `pmid`, `pmcid`, …) | External natural identifier | Keep the domain name. Do **not** rename it to `key`. Example: `Paper.doi`, `get_paper_by_doi`. |

Do **not** use `public_id` for new fields. `public_id` is a legacy name; rename it to `key` when you touch that entity.

### What `key` is not

These other uses of the word `key` stay as they are. They are **not** user-facing entity identifiers:

- Streamlit page registry: `AppPage.key`, `page_by_key`, `streamlit_page_for(key)` (page slug such as `landing`)
- Streamlit widget `key=`
- Dict keys and SQLAlchemy `Column.key` (the mapped attribute name)

A mapped attribute named `key` is allowed. The mild clash with SQLAlchemy `Column.key` is acceptable.

### URL query and helper signatures

- Query parameter: `{entity}_key` (Topic scope: `topic_scope_key`). ui-style owns how that parameter is read, written, and preserved on `st.page_link` and `st.switch_page`.
- On the ORM row, the attribute is `key` (`topic_scope.key`).
- On UI helpers that already take a page slug (`page_key`, `AppPage.key`), name the UUID argument `topic_scope_key` — **not** a bare `key=`. Example: `workflow_page_link(..., topic_scope_key=)`. A bare `key=` collides with the page slug and with Streamlit widget `key=`.
- Page-local variables that hold that UUID use `topic_scope_key` as well.

### UI copy vs code names

English captions may say **Reference id:** … That phrase is user-facing copy, not the column name. Do **not** put the private `id` in the caption. Changing that copy is a separate product decision.

### Unique constraints

Name unique constraints explicitly as `uq_{table}_{column}`, same pattern as `uq_papers_doi`.

Do **not** keep the Postgres default `{table}_{column}_key` when the column is `key` (that yields `{table}_key_key`).

## Plan slicing and outside-in implementation

How to split multi-task plans and how to implement each task. The red→green→refactor cycle and how to run tests: [tdd.md](tdd.md).

These practices are also known as **vertical slices** (plan by capability, not by technical layer), **outside-in** development (start at the system edge and drill inward), and a **walking skeleton** (a thin path through the stack that proves the feature end to end).

### When this applies

- Planning work that will be split into more than one task or commit
- Implementing features or behavior changes under `src/paper_reviewer/`

### Vertical feature slices

Each plan task delivers a **usable slice of behavior**, not a single technical layer.

**Allowed split axes** (when a feature is too large for one reviewable task):

- **Sub-feature** — e.g. first half of a form, then the rest of the same form
- **Action** — e.g. show a list of elements, then the action on one element

**Forbidden split axis:** technical layer alone (schemas-only task → ORM-only task → logic-only task).

Every slice stays complete **outside-in** for that slice: from the chosen outside edge through the layers that slice needs, until the behavior works.

### Outside edge (prefer UI)

Prefer the **UI** as the outside edge of each feature. Before treating another boundary as outside, **ask the user** how to surface the feature in the UI.

Other system boundaries (Prefect job, HTTP API, public package function used by a job) are valid outside edges when the UI is not the right edge yet. Priority order: UI first, then other boundaries the user agrees on.

### Outside-in within one task

Inside a single task, implement **layer by layer from the outside**:

1. UI (or the agreed outside boundary)
2. Package / workflow code
3. Schemas
4. Models
5. DB migrations

At each depth: write the tests for that layer, then the production code for that layer, then go one layer deeper—all in the **same** task. Do not leave schemas, models, or migrations for a later “infrastructure” task of the same plan.

### Per-task TDD

- Follow [tdd.md](tdd.md) at every depth where you add behavior.
- Write tests **immediately before** the production code they drive.
- Do **not** write tests in task N for code that belongs to a later task of the same plan. That is not TDD for that later work.

### Test design constraints

- Prefer **focused** tests with **in-memory** objects over large end-to-end tests that exercise the full database stack when thinner tests suffice.
- Use mocks or stubs **only** when the code under test crosses an **external** boundary (network, remote API). Prefer real in-memory collaborators inside the app boundary.
- Never connect to live external systems in unit or spec tests (no live network calls).

### First feature owns shared pieces

The first feature that needs a table, ORM model, schema type, or helper **owns** creating it in that feature’s vertical slice. Later features reuse what already exists; they do not assume a prior “foundation” task built those pieces in isolation.

### Do / Don’t

**Do** (vertical, outside-in):

1. Task: show a short list of papers in the UI (UI + the package/schema pieces that list needs).
2. Task: save one selected paper (UI action + package + schemas + models + migration as that save needs).

**Don’t** (horizontal layer cake):

1. Task: add Pydantic types only.
2. Task: add ORM model and migration only.
3. Task: add the archive/save function only.
4. Task: wire the UI last.

The “Don’t” shape splits one feature by layer. Agents must reject that shape when drafting or revising a plan.
