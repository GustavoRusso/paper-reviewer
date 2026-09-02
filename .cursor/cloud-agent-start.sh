#!/usr/bin/env bash
# Per-boot: start Docker if needed, wait until the daemon answers, then start
# the sandbox workspace (host/Cloud MCP). Do not run just up (Ollama model pull).
set -euo pipefail

cd "$(dirname "$0")/.."

if ! docker info >/dev/null 2>&1 && ! sudo docker info >/dev/null 2>&1; then
  sudo service docker start
fi

ready=0
for _ in $(seq 1 30); do
  if docker info >/dev/null 2>&1 || sudo docker info >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done

if [[ "${ready}" -ne 1 ]]; then
  echo "Docker daemon did not become ready" >&2
  exit 1
fi

just sandbox
