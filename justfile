# Paper Reviewer — all workflows go through these recipes.
# Do not run docker compose, uv, or python on the host directly.

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

set default-list := true
set dotenv-load := true

app_project := "paper-reviewer"
sandbox_project := "paper-reviewer-sandbox"
compose := "docker compose"
jupyter_port := env("JUPYTER_PORT", "8888")

# Build/start the persistent app stack (workspace + app profile: migrate + UI + Postgres + Prefect); wait until healthy
up:
    {{compose}} -p {{app_project}} --profile app up -d --build --wait

# Apply Alembic migrations to app Postgres (idempotent; also runs automatically on just up)
migrate:
    {{compose}} -p {{app_project}} --profile app up -d --build --wait db
    {{compose}} -p {{app_project}} --profile app run --rm --build migrate

# Pull/register the local llama3.1 model via OpenModel (idempotent; also runs on just up)
pull-model:
    {{compose}} -p {{app_project}} --profile app up -d --build --wait ollama
    {{compose}} -p {{app_project}} --profile app run --rm --build openmodel-provision

# Stop the persistent app stack; volumes are preserved
down:
    {{compose}} -p {{app_project}} down

# Follow logs (optional service name; default: all running services)
# Examples: just logs | just logs ui | just logs db | just logs prefect-server | just logs prefect-worker | just logs ollama | just logs openmodel | just logs notebooks
logs service="":
    {{compose}} -p {{app_project}} logs -f {{service}}

# Show container status for the persistent app project
status:
    {{compose}} -p {{app_project}} ps

# Interactive shell in the persistent app workspace (auto-starts if needed)
shell: up
    {{compose}} -p {{app_project}} exec -it workspace bash

# Non-interactive command in the persistent app workspace (auto-starts if needed)
# Example: just run "uv run dlthub ai status"
run *args: up
    {{compose}} -p {{app_project}} exec -T workspace sh -c '{{args}}'

# Build/start a clean sandbox workspace; wait until healthy
sandbox:
    {{compose}} -p {{sandbox_project}} up -d --build --wait

# Tear down the sandbox and delete its volumes
sandbox-down:
    {{compose}} -p {{sandbox_project}} down -v

# Interactive shell in the sandbox workspace (auto-starts if needed)
sandbox-shell: sandbox
    {{compose}} -p {{sandbox_project}} exec -it workspace bash

# Non-interactive command in the sandbox workspace (auto-starts if needed)
# Example: just sandbox-run "uv run pytest tests/search -q"
sandbox-run *args: sandbox
    {{compose}} -p {{sandbox_project}} exec -T workspace sh -c '{{args}}'

# Run pytest in the sandbox (optional path/args; fails if no tests collected)
test *args: sandbox
    {{compose}} -p {{sandbox_project}} exec -T workspace sh -c 'uv run pytest {{args}}'

# Start Jupyter Lab in the app stack (needs Postgres). Not the sandbox.
# Open http://localhost:${JUPYTER_PORT} (default 8888)
notebooks: up
    {{compose}} -p {{app_project}} --profile app --profile notebooks up -d --build --wait notebooks
    echo Jupyter Lab: http://localhost:{{jupyter_port}}
