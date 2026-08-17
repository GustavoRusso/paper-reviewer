# Agent operating instructions

This file is the single entry point for every coding agent (Cursor, Claude Code, Codex, and similar). Humans use [README.md](README.md) for a short product introduction.

Agents should always talk in ASD-STE100 Simplified Technical English.

It overrides tool-specific skills that assume a host `uv` install (including dltHub Cursor rules).

## CLI policy (mandatory)

Agent shells run on the **host**, not inside Docker. This project does **not** install `uv`, Python, or app tooling on the host.

**This file is the only place that defines agent CLI policy.** Do **not** search for, invent, or add tool-specific agent files to “enforce” it (for example `.cursor/rules/`, other IDE rule packs, or duplicate CLI checklists). If the policy must change, edit **this** section (and update [docs/local-development.md](docs/local-development.md) only when the human/local workflow description must stay in sync).

**Never** run on the host:

- `uv` / `uvx`
- `python` / `pytest` / `pip`
- `dlthub`
- raw `docker` / `docker compose` (use `just` recipes instead — including logs, `ps`, `inspect`, and health debugging)
- any command that needs Python, including pipes like `curl … | python -c "…"` and other one-liners
- API connectivity or endpoint debugging that parses JSON with Python (PubMed E-utilities probes, smoke checks, etc.)

**Always** use `just` recipes so the command runs inside the Compose `workspace` container. Host tools allowed: `just`, and `git`. `docker` / `docker compose` only appear **inside** [justfile](justfile) recipes — never as a direct agent shell command.

List recipes and descriptions: `just`. Recipe definitions: [justfile](justfile).

### Awkward or missing recipes

If the needed `just` recipe is missing, awkward, hangs (for example follow-only logs), or cannot express the task safely:

1. **Stop.** Do **not** bypass with raw `docker` / `docker compose` / host `uv` / host `python`.
2. **Tell the user** what recipe is missing or awkward and propose a concrete [justfile](justfile) change (new recipe or fix to an existing one).
3. **Wait** for agreement before editing the justfile (unless the user already asked you to add or fix that recipe).
4. After the recipe exists, use **only** that recipe for the work.

If a skill, toolkit, or third-party doc says `uv run …`, wrap it:

```bash
just run "uv run …"
# or for disposable work:
just sandbox-run "uv run …"
```

Same rule for ad-hoc probes and scripts (quote the whole in-container command):

```bash
just sandbox-run "curl -sS 'https://example.com/api' | python -c 'import sys,json; print(json.load(sys.stdin))'"
just sandbox-run "uv run python scripts/smoke_search_external_sources.py"
```

Do **not** install `uv` or Python on the host to satisfy those docs. Prefer the **sandbox** for disposable agent work; keep the persistent app (`just up`) for long-lived MCP.

Host tooling: [docs/host-requirements.md](docs/host-requirements.md). App vs sandbox lifecycle: [docs/local-development.md](docs/local-development.md).

## Documentation layout

- **[README.md](README.md)** — User-facing only: short introduction to the project (what it is, who it is for, terminology, high-level workflow). Do not put install steps, runbooks, or deep technical detail there.
- `/docs` — All other documentation (setup, workflows, architecture, operations). Agents and users share the same files; there is no separate agent-only install path.
- `/docs/specs` — Feature and workflow specs. Phase 1 (Topic definition) uses a dotted `P.S-name.md` prefix matching [README.md](README.md) (e.g. `1.1-topic-intake.md`, `1.2-topic-analysis.md`). Phase landings use `2-external-sources-ingestion.md` and `4-topic-brief-generation.md`. Phase 3 overview `3-references-selection.md` is docs-only (shared chrome; no Streamlit landing; hub opens Show references). Phase 2 uses `2.1-search-external-sources.md`, docs-only group `2.2-paper-ingestion.md`, and leaf specs `2.2.1`–`2.2.5`. Phase 3 uses `3.1-show-references.md` and `3.2-add-reference.md`. Shared **Topic scope hub** lives at `topic-scope-hub.md` (no step number). Shared local **Papers search** lives at `papers-search.md` (no step number). Shared **Paper brief** reader lives at `paper-brief.md` (no step number). External-source-specific docs live under `docs/specs/external-sources/` (no step number).
- Shared engineering practices (file moves/renames, `id` vs `key` identifier naming, plan slicing, outside-in, per-task TDD boundaries): [docs/dev-practices.md](docs/dev-practices.md).

## Feature planning and TDD (mandatory)

When **planning or implementing** app features under `src/paper_reviewer/`:

- Slice tasks and implement **outside-in** per [docs/dev-practices.md](docs/dev-practices.md) (vertical feature slices; not layer-by-layer plan tasks).
- Follow the test cycle in [docs/tdd.md](docs/tdd.md) (tests before code at each depth of the current task).

## Maintenance rules

1. **Keep docs in sync with the project.** When behavior, setup, tooling, or workflows change, update the matching document in the same change.
2. **One owner per aspect.** Each topic is specified in one and only one document. Before adding or editing, check other docs so the same facts are not duplicated; link instead of copying.
3. **Update this index** when you add, rename, or remove a documentation file under `/docs`.



## Documentation index


| Document                                                                 | Description                                                                                                                            | When to use                                                                                                                                                                                          |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [docs/host-requirements.md](docs/host-requirements.md)                   | Install Docker Desktop and `just` on the host                                                                                          | Before first local setup; whenever host tooling is missing or version guidance changes                                                                                                               |
| [docs/local-development.md](docs/local-development.md)                   | `.env` / Compose local parametrization; persistent app vs ephemeral sandbox; agent shells; running tests (`just test`); Alembic migrations; dltHub workspace + Cursor MCP enable checklist | First local config after host tools; whenever starting the workspace, opening a shell to create/modify the Python project, managing app vs sandbox, applying DB migrations, running tests, or enabling dlt-workspace-mcp |
| [docs/dev-practices.md](docs/dev-practices.md)                           | Shared engineering practices: `git mv` for tracked renames; `id` vs `key` identifier naming; vertical feature plan slices; outside-in implementation; per-task TDD boundaries | When moving or renaming tracked files; when naming entity identifiers (`id` / `key` / `doi`); when planning multi-task work or implementing features; whenever looking up repo-wide contributor/agent practices |
| [docs/technology-stack.md](docs/technology-stack.md)                     | App runtime stack and boundaries: Python, uv, Postgres (including built-in FTS for Papers search), dlt extract (load later), scispaCy, SQLAlchemy/Alembic (including no `ON DELETE CASCADE`), Streamlit, Prefect (Compose) | When adding libraries or structuring features across UI, ingest, search, DB, and jobs; when defining FKs or delete behavior |
| [docs/ui-style.md](docs/ui-style.md)                                     | Web UI semantic style: links navigate only; buttons mutate; one look per intent (primary / default / cancel / danger); Streamlit widget mapping; theme colours in `.streamlit/config.toml`; sidebar opt-in; in-page phase header/stepper | When adding or changing Streamlit buttons, page links, form submits, empty-state CTAs, or theme colours; when writing UI sections of step specs; when adding a page to (or omitting it from) the left sidebar; when adding a phase landing header or step stepper |
| [docs/project-structure.md](docs/project-structure.md)                   | Repo layout, deploy vs local-only paths, `pyproject.toml` placement, package module map (`topic_scope` steps / `schemas` / `models` including global `paper` and `paper_brief` / `ingest` / `flows`) | When adding packages/modules, deciding what Docker images copy, or where to put ORM/UI/workflow-step/ingest/flow code |
| [docs/tdd.md](docs/tdd.md)                                               | Test-First Spec Implementation (TDD): write failing tests, implement, refactor, then wire into the app; plan slicing owned by [dev-practices.md](docs/dev-practices.md) | When implementing features, behavior changes, or bug fixes under `src/paper_reviewer/` |
| [docs/specs/1.1-topic-intake.md](docs/specs/1.1-topic-intake.md) | Topic intake (phase 1 step 1): validate topic statement; insert `TopicScope`; switch to Topic analysis | When implementing or changing Topic intake, `TopicScope` create, or the intake page |
| [docs/specs/1.2-topic-analysis.md](docs/specs/1.2-topic-analysis.md) | Topic analysis (phase 1 step 2): scispaCy NER → persist `TopicFacet` rows on `TopicScope`; analysis page links to the Topic scope hub | When implementing or changing topic analysis, facet persistence, or the analysis page |
| [docs/specs/topic-scope-hub.md](docs/specs/topic-scope-hub.md) | Topic scope hub: statement, facets, action row; Home list links to the hub | When implementing or changing the Topic scope hub page or Home links to the hub |
| [docs/specs/2-external-sources-ingestion.md](docs/specs/2-external-sources-ingestion.md) | External sources ingestion phase landing: links into search external sources and later ingest pages | When implementing or changing the External sources ingestion landing |
| [docs/specs/2.1-search-external-sources.md](docs/specs/2.1-search-external-sources.md) | Search external sources (phase 2 step 1): URL `topic_scope_key` + DB facets → `search_external_sources`; dlt extract; in-memory `PaperCandidate` merge; session output cache keyed by Topic scope | When implementing or changing search orchestration, criteria input, candidate normalization, or the Search external sources page |
| [docs/specs/2.2-paper-ingestion.md](docs/specs/2.2-paper-ingestion.md) | Paper Ingestion (phase 2 step 2, docs-only group): index of archive / fulfill / brief / evaluation / indexing leaf steps; Streamlit page only for Paper archiving | When looking up the Paper Ingestion step group or its substep list |
| [docs/specs/2.2.1-paper-archiving.md](docs/specs/2.2.1-paper-archiving.md) | Paper archiving (2.2.1): Streamlit page auto-runs create-or-reuse `Paper`, then enqueues `regenerate_paper` for new / never-ingested papers and shows ingest progress | When implementing or changing paper create/reuse from candidates, `Paper` fields, archiving UI, or ingest enqueue |
| [docs/specs/2.2.2-fulfill-papers-metadata.md](docs/specs/2.2.2-fulfill-papers-metadata.md) | Fulfill papers metadata (2.2.2): `PaperAspectStatus` on `Paper`; flows `inform_source_record` / `inform_full_text` / `fulfill_paper_metadata`; `regenerate_paper` is the only force path; no dedicated page | When implementing or changing source-record or full-text fulfill, `Paper` status enums, or `regenerate_paper` |
| [docs/specs/2.2.3-generate-paper-brief.md](docs/specs/2.2.3-generate-paper-brief.md) | Generate paper brief (2.2.3): global 1:1 `PaperBrief`; gated on full text `succeeded`; topic-agnostic content; after archive, brief work is `regenerate_paper` step 3. Brief section list and LLM prompt: [src/paper_reviewer/topic_scope/generate_paper_brief/paper_brief_template.md](src/paper_reviewer/topic_scope/generate_paper_brief/paper_brief_template.md) | When implementing or changing `PaperBrief`, brief Prefect jobs, or the brief template |
| [docs/specs/2.2.4-paper-brief-evaluation.md](docs/specs/2.2.4-paper-brief-evaluation.md) | Paper brief evaluation (2.2.4): G-Eval-style LLM-as-judge of a succeeded `PaperBrief`; advisory verdict; docs-only (not implemented) | When implementing or changing paper-brief LLM-as-judge evaluation |
| [docs/specs/2.2.5-paper-indexing.md](docs/specs/2.2.5-paper-indexing.md) | Paper indexing (2.2.5): generated `keywords_tsv` + GIN from `source_record.indexing.keywords`; no Streamlit page in v1 | When implementing or changing the local Papers search document or GIN index |
| [docs/specs/3-references-selection.md](docs/specs/3-references-selection.md) | References selection phase overview (docs-only): shared header/stepper; hub opens Show references | When implementing or changing References selection phase chrome or phase entry from the hub |
| [docs/specs/3.1-show-references.md](docs/specs/3.1-show-references.md) | Show references (3.1): list References for the Topic scope from `topic_references` | When implementing or changing the Show references page or Reference list UX |
| [docs/specs/3.2-add-reference.md](docs/specs/3.2-add-reference.md) | Add reference (3.2): auto-runs Papers search and shows hits; Add / Add all attach References | When implementing or changing Add reference search results or attach UX |
| [docs/specs/papers-search.md](docs/specs/papers-search.md) | Papers search capability: Postgres FTS of topic facet concepts against `Paper.keywords_tsv` (built) | When implementing or changing local Papers search used by Add reference |
| [docs/specs/paper-brief.md](docs/specs/paper-brief.md) | Paper brief reader: hidden Streamlit page loads a succeeded global `PaperBrief` by DOI and shows structured content | When implementing or changing the Paper brief read page or the Show references **Read paper brief** link |
| [docs/specs/4-topic-brief-generation.md](docs/specs/4-topic-brief-generation.md) | Topic brief generation phase: Generate/Regenerate (blocked if zero briefed References); Prefect `create_topic_brief`; `TopicBrief`; `[n]` citations + `citation_description`; quality index deferred. Prompt: [src/paper_reviewer/topic_scope/topic_brief_generation/topic_brief_template.md](src/paper_reviewer/topic_scope/topic_brief_generation/topic_brief_template.md) | When implementing or changing Topic brief generation, `TopicBrief`, the Prefect job, or the topic-brief template |
| [docs/specs/external-sources/pubmed.md](docs/specs/external-sources/pubmed.md) | PubMed Entrez mapping to `PaperCandidate`, EFetch for source record, PMC Cloud for full text, NCBI API key / rate limits | When implementing or changing PubMed search, Entrez queries, PubMed → candidate mapping, EFetch mapping, or NCBI ops |


