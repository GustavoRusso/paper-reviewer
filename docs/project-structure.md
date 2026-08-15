# Project structure

Agents use this document when adding packages, modules, or Docker build context. It is the single source of truth for **where code lives** and **what enters production images**.

Runtime libraries and layer boundaries: [technology-stack.md](technology-stack.md). Local Compose/`just` workflows: [local-development.md](local-development.md).

## Layout principles

- **src layout** — One installable package under `src/`. Tests and docs stay outside it so accidental imports from the working tree do not mask the installed package.
- **One package, several entrypoints** — Streamlit, Prefect workers, and migrations install the same package and differ by process command, not by separate Python projects.
- **Docker is the deploy gate** — Production images copy only runtime paths. Development files stay in the repo and are excluded via `.dockerignore`.

Package name: **`paper_reviewer`** (snake_case). Imports look like `from paper_reviewer.models import ...`.

## `pyproject.toml`

Use a **single** [`pyproject.toml`](../pyproject.toml) at the **repository root**, next to `Dockerfile`, `compose.yml`, and `uv.lock`.

| Placement | Rule |
| --- | --- |
| Repo root | **Required.** One dependency set, one `uv.lock`, one editable install of `paper_reviewer`. |
| Inside `src/` | **Forbidden.** `src/` holds importable packages only; tooling expects project metadata at the root. |
| Multiple files (workspace / multi-package) | **Not used.** Domain areas share schemas and ORM models; split only if a piece later becomes a separately versioned product. |

Domain boundaries are Python **subpackages** (`topic_brief_generation`, `models`, `schemas`, `ingest`, `ui`, `flows`, `db`), not separate installable projects.

## Deploy boundary

```mermaid
flowchart TB
  subgraph deploy [Copied into production images]
    srcPkg["src/paper_reviewer/"]
    alembicDir["alembic/ + alembic.ini"]
    deps["pyproject.toml + uv.lock"]
    streamlitTheme[".streamlit/config.toml"]
  end

  subgraph localOnly [Repo-only / not in prod images]
    testsDir["tests/"]
    docsDir["docs/"]
    hostTools["justfile, AGENTS.md, README.md"]
    composeFiles["compose.yml, .env examples"]
  end

  Dockerfile -->|"COPY + .dockerignore"| deploy
  composeFiles --> Dockerfile
```

| Category | Paths | Role |
| --- | --- | --- |
| **Runtime (deployed)** | `src/paper_reviewer/`, `alembic/`, `alembic.ini`, `pyproject.toml`, `uv.lock`, `.streamlit/config.toml` | What production containers need to run the UI, flows, ingest, and migrations. Streamlit theme: [ui-style.md](ui-style.md) |
| **Build / orchestration** | `Dockerfile`, `compose.yml`, `.dockerignore`, `justfile` | Image build and local workflows on the host; not application runtime code |
| **Development-only** | `tests/`, `docs/`, `AGENTS.md`, `README.md`, seed/fixtures under `tests/` or non-copied `scripts/` | Docs, tests, and agent guidance; exclude from production images |

Production Dockerfiles copy only the runtime set. `.dockerignore` excludes `tests/`, `docs/`, `AGENTS.md`, `.git/`, and similar paths.

**Target:** one application image; multiple Compose services with different entrypoints (Streamlit, Prefect worker, Alembic migrate)—same tree, different `CMD`.

**Current Compose services** (names, profiles, ports, migrate-before-ui): owned by [local-development.md](local-development.md). Do not restate that inventory here.

## Target tree

```text
paper-reviewer/
├── src/
│   └── paper_reviewer/                 # installable package (deployed)
│       ├── __init__.py
│       ├── topic_brief_generation/     # Topic brief generation step behavior
│       │   ├── topic_intake/
│       │   ├── topic_analysis/
│       │   ├── related_paper_search/
│       │   ├── retrieval_triage/
│       │   ├── paper_archiving/        # Paper archiving (create-or-reuse Paper)
│       │   ├── fulfill_papers_metadata/   # Fulfill papers metadata (source record + full text)
│       │   ├── generate_paper_brief/   # Generate paper brief (PaperBrief)
│       │   └── topic_brief/
│       ├── schemas/
│       │   └── topic_brief_generation/ # Pydantic contracts for that workflow
│       ├── models/
│       │   ├── base.py                 # DeclarativeBase (all workflows)
│       │   ├── paper.py                # Global Paper ORM (not owned by a Topic scope)
│       │   ├── paper_brief.py          # Global PaperBrief ORM (not owned by a Topic scope)
│       │   └── topic_brief_generation/ # ORM for that workflow (TopicScope, topic_facets)
│       ├── ingest/                     # dlt paper-source extract (shared)
│       ├── ui/                         # Streamlit
│       ├── flows/                      # Prefect flows (source record, full text, briefs, orchestrators)
│       └── db/                         # engine, session, URL helpers
├── alembic/
│   └── versions/
├── alembic.ini
├── .streamlit/
│   └── config.toml                     # Streamlit theme (cwd; colour tokens in ui-style.md)
├── tests/                              # mirrors package layout (not deployed)
│   ├── topic_brief_generation/
│   ├── schemas/
│   ├── models/
│   ├── ingest/
│   ├── ui/
│   └── flows/
├── docs/
├── Dockerfile
├── .dockerignore
├── compose.yml
├── justfile
├── pyproject.toml
├── uv.lock
├── README.md
└── AGENTS.md
```

Tests live under `tests/` and mirror the package layout. Agents write those specs first when changing app behavior—see [tdd.md](tdd.md).

## Module map

Aligned with [technology-stack.md](technology-stack.md) boundaries:

| Stack piece | Package path | Owns |
| --- | --- | --- |
| Topic brief generation steps | `paper_reviewer.topic_brief_generation.<step>` | Step behavior for the README workflow (intake, analysis, related-paper search, triage, paper archiving, fulfill papers metadata, generate paper brief, topic brief). Specs: [specs/1.1-topic-intake.md](specs/1.1-topic-intake.md), [specs/1.2-topic-analysis.md](specs/1.2-topic-analysis.md), [specs/2-paper-ingestion.md](specs/2-paper-ingestion.md), [specs/3-paper-search.md](specs/3-paper-search.md), [specs/4-topic-brief.md](specs/4-topic-brief.md), [specs/03-related-paper-search.md](specs/03-related-paper-search.md), [specs/04-retrieval-triage.md](specs/04-retrieval-triage.md), [specs/05-paper-archiving.md](specs/05-paper-archiving.md), [specs/06-fulfill-papers-metadata.md](specs/06-fulfill-papers-metadata.md), [specs/07-generate-paper-brief.md](specs/07-generate-paper-brief.md). |
| Pydantic | `paper_reviewer.schemas.<workflow>` | Domain contracts mirrored under the workflow name (e.g. `schemas.topic_brief_generation.topic_analysis`). |
| SQLAlchemy ORM | `paper_reviewer.models.<workflow>` plus global `models.paper` / `models.paper_brief` | Workflow table mappings under the workflow name; global `Paper` / `PaperBrief` at top-level `models`. `models.base` is shared. Thin create/get only. |
| dlt | `paper_reviewer.ingest` | Paper-source dlt sources/resources (extract; Postgres load when adopted) |
| Streamlit | `paper_reviewer.ui` | Presentation and user interaction only |
| Prefect | `paper_reviewer.flows` | `inform_source_record`, `inform_full_text`, `fulfill_paper_metadata`, `create_paper_brief`, `regenerate_paper` |
| DB plumbing | `paper_reviewer.db` | Engine/session helpers; not ORM entities |
| Alembic | repo-root `alembic/` | DDL versioning against `models` metadata |

### Workflow packages vs cross-cutting (agent rule)

1. **Each product workflow is a named top-level package** (today: `topic_brief_generation`; later siblings)—not a generic `steps` bag.
2. **Step behavior** lives only under that workflow package (`topic_brief_generation.<step>`).
3. **Cross-cutting stays top-level** — `schemas`, `models`, `ingest`, `ui`, `db`, `flows` (never nest these under a workflow behavior package).
4. **Mirror under** `schemas/<workflow>/` and `models/<workflow>/` — domain types vs ORM mappings; never put Pydantic or ORM inside the behavior package. **Exception:** global tables that a workflow does not own (`Paper`, `PaperBrief`) live at `models.paper` and `models.paper_brief`, not under `models/<workflow>/`.
5. **`models.base`** is shared across workflows. This workflow’s Topic scope root is `models.topic_brief_generation.topic_scope` (`TopicScope`). Facet rows are `models.topic_brief_generation.topic_analysis` (`topic_facets`).
6. **Stubs OK** for unimplemented steps; do not invent behavior without a spec + TDD ([tdd.md](tdd.md)).

### `models` vs `schemas` (agent rule)

- **`schemas`** — portable domain contracts (Pydantic). Workflow steps, tests, and dlt yields use these shapes. Prefer one schema source; do **not** add a parallel pure domain-entity layer.
- **`models`** — Postgres persistence (SQLAlchemy) plus thin create/get helpers. Map to/from `schemas` at the boundary; do **not** put analysis, search, or merge logic here.
- **Behavior** — named workflow step packages (and shared `ingest` / later `flows`), not fat ORM classes and not a separate `domain/` package.

## Naming conventions

- Repo directory: `paper-reviewer` (kebab-case)
- Import package: `paper_reviewer` (snake_case)
- Workflow packages: product term in snake_case (`topic_brief_generation`)
- Cross-cutting subpackages: short plural nouns (`models`, `schemas`, `flows`)
- Do not use vague roots such as `src/app`, `src/code`, or nested `src/src`
- Entity identifiers (`id` vs minted `key` vs domain names such as `doi`): [dev-practices.md](dev-practices.md#identifier-naming-id-vs-key)
