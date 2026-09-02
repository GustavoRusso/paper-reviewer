# Paper Reviewer — testers use `just up` (product stack).
# Develop/test uses sandbox recipes (`just test`, `just run`, `just shell`).
# Same recipe names inside the workspace image (PAPER_REVIEWER_IN_CONTAINER=1).
# Do not run docker compose, uv, or python on the host directly.

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

set default-list := true
set dotenv-load := true

# Compose sets this on the workspace service. Do not put it in .env.
in_container := env("PAPER_REVIEWER_IN_CONTAINER", "")

app_project := "paper-reviewer"
sandbox_project := "paper-reviewer-sandbox"
compose := "docker compose"
jupyter_port := env("JUPYTER_PORT", "8888")

host_only_error := "Run this recipe on the host (Docker Desktop or Cloud VM), not inside the workspace container."

[private]
[unix]
_require-host:
    #!/usr/bin/env bash
    if [ "{{ in_container }}" = "1" ]; then
      echo "{{ host_only_error }}" >&2
      exit 1
    fi

[private]
[windows]
_require-host:

# Windows always uses Compose (the IDE is never Windows-inside-container).
[private]
[unix]
_ensure-sandbox:
    @{{ if in_container == "1" { "true" } else { quote(just_executable()) + " sandbox" } }}

# Build/start the persistent app stack (workspace + UI + Postgres + Prefect); wait until healthy
up: _require-host
    {{ compose }} -p {{ app_project }} --profile app up -d --build --wait

# Apply Alembic migrations to app Postgres (manual one-off step; not part of app startup)
migrate: _require-host
    {{ compose }} -p {{ app_project }} --profile app up -d --build --wait workspace db
    {{ compose }} -p {{ app_project }} exec -T workspace sh /workspace/scripts/migrate.sh

# Pull a local Ollama model (idempotent). Default: gemma4:e4b
# Usage: just pull-model
#        just pull-model "llama3.1:8b"
# Quote the tag (colon). Examples:
#   gemma4:e4b         — default; best measured paper-brief quality
#   llama3.1:8b        — prior offline-eval baseline
#   qwen2.5:0.5b       — ~1 GB RAM; smoke tests only
#   qwen2.5-coder:7b   — ~8 GB NVIDIA; structured/technical text
#   qwen2.5:7b         — ~8 GB NVIDIA; general paper-brief alternative
# After pull: set OPENAI_MODEL to the same tag in .env; recreate prefect-worker.
pull-model model="gemma4:e4b": _require-host
    {{ compose }} -p {{ app_project }} --profile app up -d --wait ollama
    {{ compose }} -p {{ app_project }} --profile app exec -T ollama ollama pull {{ model }}

# Stop the persistent app stack; volumes are preserved
down: _require-host
    {{ compose }} -p {{ app_project }} down

# Follow logs (optional service name; default: all running services)
# Examples: just logs | just logs ui | just logs db | just logs prefect-server | just logs prefect-worker | just logs ollama | just logs notebooks
logs service="": _require-host
    {{ compose }} -p {{ app_project }} logs -f {{ service }}

# Show container status for the persistent app project
status: _require-host
    {{ compose }} -p {{ app_project }} ps

# Interactive shell in the sandbox workspace (auto-starts if needed)
[unix]
shell: _ensure-sandbox
    {{ if in_container == "1" { "bash" } else { compose + " -p " + sandbox_project + " exec -it workspace bash" } }}

[windows]
shell: sandbox
    {{ compose }} -p {{ sandbox_project }} exec -it workspace bash

alias sandbox-shell := shell

# Non-interactive command in the sandbox workspace (auto-starts if needed)
# Example: just run "uv run dlthub ai status"
[unix]
run *args: _ensure-sandbox
    {{ if in_container == "1" { "sh -c " + quote(args) } else { compose + " -p " + sandbox_project + " exec -T workspace sh -c " + quote(args) } }}

[windows]
run *args: sandbox
    {{ compose }} -p {{ sandbox_project }} exec -T workspace sh -c '{{ args }}'

alias sandbox-run := run

# Build/start a clean sandbox workspace; wait until healthy
sandbox: _require-host
    {{ compose }} -p {{ sandbox_project }} up -d --build --wait

# Tear down the sandbox and delete its volumes
sandbox-down: _require-host
    {{ compose }} -p {{ sandbox_project }} down -v

# Run pytest in the sandbox (optional path/args; fails if no tests collected)
[unix]
test *args: _ensure-sandbox
    {{ if in_container == "1" { "uv run pytest " + args } else { compose + " -p " + sandbox_project + " exec -T workspace sh -c " + quote("uv run pytest " + args) } }}

[windows]
test *args: sandbox
    {{ compose }} -p {{ sandbox_project }} exec -T workspace sh -c 'uv run pytest {{ args }}'

# Start Jupyter Lab in the app stack (needs Postgres). Not the sandbox.
# Open http://localhost:${JUPYTER_PORT} (default 8888)
notebooks: up
    {{ compose }} -p {{ app_project }} --profile app --profile notebooks up -d --build --wait notebooks
    echo Jupyter Lab: http://localhost:{{ jupyter_port }}
