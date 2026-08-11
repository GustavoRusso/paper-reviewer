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
