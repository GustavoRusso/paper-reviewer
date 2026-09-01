#!/usr/bin/env bash
# Per-boot: start Docker and wait until the daemon answers.
# Do not run just up here (Ollama model pull is large).
set -euo pipefail

if docker info >/dev/null 2>&1; then
  exit 0
fi

sudo service docker start

for _ in $(seq 1 30); do
  if docker info >/dev/null 2>&1; then
    exit 0
  fi
  if sudo docker info >/dev/null 2>&1; then
    exit 0
  fi
  sleep 1
done

echo "Docker daemon did not become ready" >&2
exit 1
