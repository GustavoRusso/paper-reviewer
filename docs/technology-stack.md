# Technology stack

Agents use this document when choosing libraries or structuring features. It is the single source of truth for the **application** runtime stack.

Host tooling (Docker Desktop, `just`), repo layout, and local workflows live elsewhere:

- [host-requirements.md](host-requirements.md) — what belongs on the host
- [justfile](../justfile) — recipe definitions (`just` to list them)
- [local-development.md](local-development.md) — app vs sandbox lifecycle
- [project-structure.md](project-structure.md) — package layout and what enters production images

All stack components below run **inside Docker images**. Do not install Python, uv, or app frameworks on the host. Bootstrap and package work happens in the Compose `workspace` image via `just shell` / `just sandbox-shell` ([local-development.md](local-development.md)).

## Stack

| Component | Tool | Responsibility |
| --- | --- | --- |
| Language / validation | Python + Pydantic | Runtime and shared schemas (inputs, paper models, dlt resources) |
| Package manager | uv | Dependencies and virtualenvs inside container images |
| Relational database | PostgreSQL | Papers, briefs, citations, job-related app data |
| Data ingestion | dlt (dlthub) + Pydantic | Load from paper sources into Postgres; workspace uses `dlt[hub]` and the Cursor rest-api-pipeline toolkit |
| ORM / DB access | SQLAlchemy | Models and application reads/writes |
| Schema migrations | Alembic | Versioned DDL against SQLAlchemy metadata |
| Web UI | Streamlit | User-facing research workflows |
| Job orchestrator | Prefect | Search, ingest, and brief-generation pipelines |
| Tests | pytest | Specs and regression tests for `paper_reviewer` (dev-only; run via `just test` in the sandbox) |

## Layer sketch

```mermaid
flowchart TB
  ui[Streamlit]
  orch[Prefect flows]
  ingest[dlt ingest]
  orm[SQLAlchemy queries]
  db[(PostgreSQL)]
  mig[Alembic migrations]

  ui --> orch
  orch --> ingest
  orch --> orm
  ui --> orm
  ingest --> db
  orm --> db
  mig --> db
```

## Boundaries

- **Pydantic** — Validate and define data shapes shared across UI, pipelines, and ingest. Prefer one schema source over ad-hoc dicts.
- **dlt** — Source → Postgres loads only. Define resource schemas with Pydantic; do not use dlt for ordinary app CRUD.
- **SQLAlchemy** — Application reads and writes (Streamlit, Prefect tasks that are not bulk ingest).
- **Alembic** — Owns relational schema versioning. dlt loads into tables that already match that schema; do not let dlt freely evolve production DDL against Alembic.
- **Foreign keys — no `ON DELETE CASCADE`** — Never use `ON DELETE CASCADE` in Alembic or SQLAlchemy (`ForeignKey(..., ondelete="CASCADE")`, or relationship cascades that delete children when the parent is deleted). Keep the database default (`NO ACTION` / `RESTRICT`) so the database rejects deleting a parent that still has children. When a parent must be removed, delete or reassign child rows explicitly in application code first, then delete the parent. Do not restate this ban in feature specs; follow it for all schema work.
- **Prefect** — Orchestrate long-running or multi-step jobs (search, ingest, briefs). Trigger from the UI or schedules; keep business steps in flows/tasks, not in Streamlit callbacks alone.
- **Streamlit** — Presentation and user interaction only. Delegate heavy work to Prefect; persist via SQLAlchemy (or kick off dlt through Prefect).
- **pytest** — Specs and regressions under `tests/` (mirrors `src/paper_reviewer/`). Prefer pytest style (`assert`, fixtures) over `unittest.TestCase`. Fake boundary I/O (no live paper-source HTTP). Keep Streamlit thin and test schemas/domain/flows rather than widget chrome. Do not unit-test third-party library internals. Agents follow [tdd.md](tdd.md) for the Test-First Spec workflow.

## Out of scope here

Install steps, Compose projects, and `just` recipes are not documented in this file. See [host-requirements.md](host-requirements.md), [justfile](../justfile), and [local-development.md](local-development.md). The TDD process for agents is in [tdd.md](tdd.md).
