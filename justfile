# Paper Reviewer — all workflows go through these recipes.
# Do not run docker compose, uv, or python on the host directly.

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

set default-list := true

app_project := "paper-reviewer"
sandbox_project := "paper-reviewer-sandbox"
compose := "docker compose"

# Build/start the persistent app workspace; wait until healthy
up:
    {{compose}} -p {{app_project}} up -d --build --wait

# Stop the persistent app stack; volumes are preserved
down:
    {{compose}} -p {{app_project}} down

# Follow logs (optional service name; default: workspace)
logs service="workspace":
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

# Run pytest in the sandbox (optional path/args; exit 5 = no tests = success)
test *args: sandbox
    {{compose}} -p {{sandbox_project}} exec -T workspace sh -c 'uv run pytest {{args}}; e=$?; [ "$e" -eq 0 ] || [ "$e" -eq 5 ]'
