# Agent documentation map

This file is for coding agents. Humans use [README.md](README.md) for a quick product introduction; agents use this map to find the right documentation and keep it accurate.

## Documentation layout

- **[README.md](README.md)** — User-facing only: short introduction to the project (what it is, who it is for, terminology, high-level workflow). Do not put install steps, runbooks, or deep technical detail there.
- **`/docs`** — All other documentation (setup, workflows, architecture, operations). Agents and users share the same files; there is no separate agent-only install path.
- **`/docs/specs`** — Feature and workflow specs. Paper-source-specific search criteria live under `docs/specs/paper-sources/`.

## Maintenance rules

1. **Keep docs in sync with the project.** When behavior, setup, tooling, or workflows change, update the matching document in the same change.
2. **Single source of truth.** Before adding or editing content, check other docs and the README so the same facts are not duplicated. Prefer linking to the authoritative document over copying text.
3. **Update this index** when you add, rename, or remove a documentation file under `/docs`.

## Documentation index

| Document | Description | When to use |
| --- | --- | --- |
| [docs/host-requirements.md](docs/host-requirements.md) | Install Docker Desktop and `just` on the host | Before first local setup; whenever host tooling is missing or version guidance changes |
| [docs/local-development.md](docs/local-development.md) | Persistent app vs ephemeral sandbox; `just` recipes; `shell` / `sandbox-shell` for in-container bootstrap | After host tools are installed; whenever starting the workspace, opening a shell to create/modify the Python project, or managing app vs sandbox |
| [docs/technology-stack.md](docs/technology-stack.md) | App runtime stack: Python, uv, Postgres, dlt, SQLAlchemy/Alembic, Streamlit, Prefect | When adding libraries or structuring features across UI, ingest, DB, and jobs |
| [docs/project-structure.md](docs/project-structure.md) | Repo layout, deploy vs local-only paths, `pyproject.toml` placement, package module map | When adding packages/modules, deciding what Docker images copy, or where to put ORM/UI/ingest/flow code |
| [docs/tdd.md](docs/tdd.md) | Test-First Spec Implementation (TDD): write failing tests, implement, refactor, then wire into the app | When implementing features, behavior changes, or bug fixes under `src/paper_reviewer/` |
| [docs/specs/related-paper-search.md](docs/specs/related-paper-search.md) | Related-paper search workflow: generic criteria, dlt extract across sources, `PaperCandidate` merge | When implementing or changing search orchestration, criteria input, or candidate normalization |
| [docs/specs/paper-sources/pubmed.md](docs/specs/paper-sources/pubmed.md) | PubMed paper-source search criteria and E-utilities mapping to `PaperCandidate` | When implementing or changing PubMed search, Entrez queries, or PubMed → candidate mapping |
