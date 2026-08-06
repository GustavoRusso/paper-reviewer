# Local development

All local workflows run through `just` recipes that wrap Docker Compose. Install host tools first: [host-requirements.md](host-requirements.md).

Do **not** run `docker compose`, language runtimes, or package managers on the host. Use `just` recipes instead. List them with `just`; definitions live in [justfile](../justfile).

## Current stack

Compose currently defines a single **`workspace`** service: a Python 3.12 + uv image with the repository bind-mounted at `/workspace`. There is no Postgres or application (`app`) service yet.

Use `just shell` / `just sandbox-shell` for interactive work, or `just run` / `just sandbox-run` for non-interactive commands (for example `uv init`, installing packages, or configuring dlt). Changes under `/workspace` persist on the host.

## Agent shells

Coding-agent terminals (Cursor, Claude Code, Codex, and similar) run on the **host**, not inside the Compose container. The Linux `.venv` and `uv` binary exist only in the image, so host `uv` / `python` / `pytest` will fail.

Follow [AGENTS.md](../AGENTS.md): wrap every in-container command with `just`. Prefer `just sandbox-run` / `just test` for disposable agent work. Keep the persistent app (`just up`) for long-lived MCP so `just sandbox-down` does not tear it down.

Postgres, Streamlit/Prefect app services, seeding, and `just reset` will be added later.

## Two environments

| Environment | Compose project | Data | When to use |
| --- | --- | --- | --- |
| **Persistent app** | `paper-reviewer` | Named volumes survive `just down` (when volumes exist) | End-user local use; keep data between sessions |
| **Ephemeral sandbox** | `paper-reviewer-sandbox` | Volumes removed on teardown | Agents, CI, bug reproduction, disposable experiments |

Both share the same [compose.yml](../compose.yml). Isolation comes from the Compose **project name** (`-p`), so wiping the sandbox never deletes app data.

```mermaid
flowchart LR
  justRecipes[just recipes]
  appProject["compose -p paper-reviewer"]
  sandboxProject["compose -p paper-reviewer-sandbox"]
  namedVol[named volumes kept]
  throwawayVol["volumes removed with -v"]

  justRecipes --> appProject
  justRecipes --> sandboxProject
  appProject --> namedVol
  sandboxProject --> throwawayVol
```

Agents should prefer the sandbox for disposable work so the persistent app project stays untouched when both stacks run on the same machine. For when and how to write tests before implementing app behavior, see [tdd.md](tdd.md). For the cross-tool CLI harness, see [AGENTS.md](../AGENTS.md).

## dltHub workspace and Cursor AI workbench

This repo is a **dltHub workspace** (marker: [`.dlt/.workspace`](../.dlt/.workspace)). App Python work still runs in Compose via `just`; do not install a second app toolchain on the host for day-to-day coding.

### Bootstrap (already applied for this project)

These were run inside the sandbox `workspace` container (repo bind-mounted at `/workspace`):

```bash
just sandbox
# then in the container (e.g. just sandbox-shell):
uvx dlthub-init@latest
uv add "dlt[hub]"
uv add fastmcp
uv run dlthub ai init --agent cursor
uv run dlthub ai toolkit install rest-api-pipeline
```

That creates/updates the workspace marker, `.dlt` config, Cursor skills/rules under [`.cursor/`](../.cursor/), MCP config [`.cursor/mcp.json`](../.cursor/mcp.json), and the **rest-api-pipeline** toolkit. The workspace image includes `git` because `dlthub ai init` clones the workbench repo.

Re-check status anytime:

```bash
just sandbox-run "uv run dlthub ai status"
```

Or with an interactive shell: `just sandbox-shell`, then `uv run dlthub ai status`.

### Enable the dlt-workspace-mcp server in Cursor (manual)

MCP is configured to run **inside the Compose `workspace` container** (no host `uv`). See [`.cursor/mcp.json`](../.cursor/mcp.json).

1. Start the persistent app workspace so the container is running:

   ```bash
   just up
   ```

   (`docker compose exec` only works against a running service. Prefer the **paper-reviewer** project over the sandbox so MCP is not torn down by `just sandbox-down`.)

2. Open this project in **Cursor**.
3. Open **Cursor Settings → MCP**.
4. Find **`dlt-workspace-mcp`** and **Enable** / approve it if prompted.
5. Confirm status is connected (not error / needsAuth).
6. Start a **new Agent** chat in this project (Agent mode, not plain Chat) so skills, rules, and MCP tools load.
7. Smoke-check: ask the agent to use workspace MCP tools (e.g. list pipelines) once any pipeline exists.

If the server fails to start:

- Error `service "shell" is not running` / unknown service: the Compose service name is **`workspace`**, not `shell` (see `compose.yml`). Reload MCP after fixing `.cursor/mcp.json`.
- Error `service "workspace" is not running`: run `just up`, wait until healthy (`just status`), then toggle the MCP server off/on or reload the Cursor window.
- Confirm `fastmcp` is installed in the project env (`uv add fastmcp` inside `just shell` if missing).
- Re-run `uv run dlthub ai init --agent cursor` in the workspace container only if you need to regenerate skills/rules; keep the Docker-based `mcp.json` (do not let init overwrite it back to host `uv` without re-applying the compose exec form).
- Run `uv run dlthub ai status` inside the container for diagnostics.

Official references: [REST API Source with dltHub AI Workbench](https://dlthub.com/docs/hub/ingestion/rest-api-source), [Installation](https://dlthub.com/docs/hub/getting-started/installation).
