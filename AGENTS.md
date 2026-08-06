# Agent operating instructions

This file is the single entry point for every coding agent (Cursor, Claude Code, Codex, and similar). Humans use [README.md](README.md) for a short product introduction.

It overrides tool-specific skills that assume a host `uv` install (including dltHub Cursor rules).

## CLI policy (mandatory)

Agent shells run on the **host**, not inside Docker. This project does **not** install `uv`, Python, or app tooling on the host.

**Never** run on the host:

- `uv` / `uvx`
- `python` / `pytest`
- `dlthub`
- raw `docker compose` (use `just` recipes instead)

**Always** use `just` recipes. Host tools allowed: `just`, `docker` / `docker compose` only when a recipe wraps them, and `git`.

List recipes and descriptions: `just`. Recipe definitions: [justfile](justfile).

If a skill, toolkit, or third-party doc says `uv run …`, wrap it:

```bash
just run "uv run …"
# or for disposable work:
just sandbox-run "uv run …"
```

Do **not** install `uv` or Python on the host to satisfy those docs. Prefer the **sandbox** for disposable agent work; keep the persistent app (`just up`) for long-lived MCP.

Host tooling: [docs/host-requirements.md](docs/host-requirements.md). App vs sandbox lifecycle: [docs/local-development.md](docs/local-development.md).

## Documentation layout

- **[README.md](README.md)** — User-facing only: short introduction to the project (what it is, who it is for, terminology, high-level workflow). Do not put install steps, runbooks, or deep technical detail there.
- **`/docs`** — All other documentation (setup, workflows, architecture, operations). Agents and users share the same files; there is no separate agent-only install path.
- **`/docs/specs`** — Feature and workflow specs. Paper-source-specific search criteria live under `docs/specs/paper-sources/`.

## Maintenance rules

1. **Keep docs in sync with the project.** When behavior, setup, tooling, or workflows change, update the matching document in the same change.
2. **One owner per aspect.** Each topic is specified in one and only one document. Before adding or editing, check other docs so the same facts are not duplicated; link instead of copying.
3. **Update this index** when you add, rename, or remove a documentation file under `/docs`.

## Documentation index

| Document | Description | When to use |
| --- | --- | --- |
| [docs/host-requirements.md](docs/host-requirements.md) | Install Docker Desktop and `just` on the host | Before first local setup; whenever host tooling is missing or version guidance changes |
| [docs/local-development.md](docs/local-development.md) | Persistent app vs ephemeral sandbox; agent shells; dltHub workspace + Cursor MCP enable checklist | After host tools are installed; whenever starting the workspace, opening a shell to create/modify the Python project, managing app vs sandbox, or enabling dlt-workspace-mcp |
| [docs/technology-stack.md](docs/technology-stack.md) | App runtime stack: Python, uv, Postgres, dlt/dltHub, SQLAlchemy/Alembic, Streamlit, Prefect | When adding libraries or structuring features across UI, ingest, DB, and jobs |
| [docs/project-structure.md](docs/project-structure.md) | Repo layout, deploy vs local-only paths, `pyproject.toml` placement, package module map | When adding packages/modules, deciding what Docker images copy, or where to put ORM/UI/ingest/flow code |
| [docs/tdd.md](docs/tdd.md) | Test-First Spec Implementation (TDD): write failing tests, implement, refactor, then wire into the app | When implementing features, behavior changes, or bug fixes under `src/paper_reviewer/` |
| [docs/specs/related-paper-search.md](docs/specs/related-paper-search.md) | Related-paper search workflow: generic criteria, dlt extract across sources, `PaperCandidate` merge | When implementing or changing search orchestration, criteria input, or candidate normalization |
| [docs/specs/paper-sources/pubmed.md](docs/specs/paper-sources/pubmed.md) | PubMed paper-source search criteria and E-utilities mapping to `PaperCandidate` | When implementing or changing PubMed search, Entrez queries, or PubMed → candidate mapping |
