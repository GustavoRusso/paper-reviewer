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

Domain boundaries are Python **subpackages** (`models`, `schemas`, `topic_analysis`, `ingest`, `search`, `ui`, `flows`), not separate installable projects.

## Deploy boundary

```mermaid
flowchart TB
  subgraph deploy [Copied into production images]
    srcPkg["src/paper_reviewer/"]
    alembicDir["alembic/ + alembic.ini"]
    deps["pyproject.toml + uv.lock"]
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
| **Runtime (deployed)** | `src/paper_reviewer/`, `alembic/`, `alembic.ini`, `pyproject.toml`, `uv.lock` | What production containers need to run the UI, flows, ingest, and migrations |
| **Build / orchestration** | `Dockerfile`, `compose.yml`, `.dockerignore`, `justfile` | Image build and local workflows on the host; not application runtime code |
| **Development-only** | `tests/`, `docs/`, `AGENTS.md`, `README.md`, seed/fixtures under `tests/` or non-copied `scripts/` | Docs, tests, and agent guidance; exclude from production images |

Production Dockerfiles copy only the runtime set. `.dockerignore` excludes `tests/`, `docs/`, `AGENTS.md`, `.git/`, and similar paths.

**Target:** one application image; multiple Compose services with different entrypoints (Streamlit, Prefect worker, Alembic migrate)—same tree, different `CMD`.

**Current Compose services** (names, profiles, ports, migrate-before-ui): owned by [local-development.md](local-development.md). Do not restate that inventory here.

## Target tree

```text
paper-reviewer/
├── src/
│   └── paper_reviewer/           # installable package (deployed)
│       ├── __init__.py
│       ├── models/               # SQLAlchemy ORM ↔ Postgres (+ TopicBriefGeneration helpers)
│       │   ├── __init__.py
│       │   └── base.py           # DeclarativeBase, shared metadata
│       ├── schemas/              # shared Pydantic models
│       ├── topic_analysis/       # Topic analysis analyzer + persist helpers
│       ├── ingest/               # dlt sources / resources (extract)
│       ├── search/               # related-paper search orchestration / merge
│       ├── ui/                   # Streamlit app entry + pages
│       ├── flows/                # Prefect flows and tasks (planned)
│       └── db/                   # engine, session, URL helpers
├── alembic/                      # migrations (deployed)
│   └── versions/
├── alembic.ini
├── tests/                        # mirrors package layout (not deployed)
│   ├── models/
│   ├── topic_analysis/
│   ├── ingest/
│   ├── search/
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
| SQLAlchemy ORM | `paper_reviewer.models` | Table-mapped classes (e.g. `TopicBriefGeneration`, facet rows) plus generation helpers in `topic_brief_generation.py` (intake start; later workflow orchestration as needed — does **not** convert `TopicAnalysisResult` → `SearchCriteria`) |
| Pydantic | `paper_reviewer.schemas` | Shared validated shapes: `TopicStatement`; `TopicFacet` / `TopicAnalysisResult` / `SearchCriteria` / source overrides / `RelatedPaperSearchResult` in `schemas.search`; `PaperCandidate` in `schemas.candidate`; future brief shapes. Topic analysis types live under `schemas.search` because search consumes them. |
| Topic analysis | `paper_reviewer.topic_analysis` | Analyzer (`analyze_topic_statement` or equivalent) and persist helper (`run_topic_analysis` or equivalent). Behavior: [specs/topic-analysis.md](specs/topic-analysis.md). NER library: [technology-stack.md](technology-stack.md). Does **not** build `SearchCriteria`. |
| dlt | `paper_reviewer.ingest` | Paper-source dlt sources/resources (extract; Postgres load when adopted) |
| Related-paper search | `paper_reviewer.search` | Orchestration, registry, merge of `PaperCandidate` lists. **Accepts** `TopicAnalysisResult`; converts internally to `SearchCriteria` when needed. |
| Streamlit | `paper_reviewer.ui` | Presentation and user interaction only |
| Prefect | `paper_reviewer.flows` | Search, ingest, and brief pipelines (planned) |
| DB plumbing | `paper_reviewer.db` | Engine/session helpers; not ORM entities |
| Alembic | repo-root `alembic/` | DDL versioning against `models` metadata |

## Naming conventions

- Repo directory: `paper-reviewer` (kebab-case)
- Import package: `paper_reviewer` (snake_case)
- Subpackages: short plural nouns for collections (`models`, `schemas`, `flows`)
- Do not use vague roots such as `src/app`, `src/code`, or nested `src/src`
