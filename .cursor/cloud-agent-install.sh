#!/usr/bin/env bash
# Idempotent Cloud Agent install: local Compose env file only.
# Host Docker and just come from .cursor/Dockerfile.
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env && -f .env.example ]]; then
  cp .env.example .env
fi
