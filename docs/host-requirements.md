# Host requirements

Install these tools on your machine before any Paper Reviewer workflow. They are the **only** host requirements.

## What belongs on the host

| Tool | Role |
| --- | --- |
| **Docker Desktop** | Runs the entire development and application stack in containers (WSL2 backend recommended on Windows). |
| **`just`** | Single command interface for every project workflow. |

Do **not** install frameworks, languages, compilers, runtimes, or other app tooling on the host. Anything needed to develop or run the app must live inside Docker images.

Cursor Cloud Agent VMs install Docker Engine and `just` from [`.cursor/environment.json`](../.cursor/environment.json). You do not install those tools by hand on the Cloud VM. See [local-development.md — Cursor Cloud Agents](local-development.md#cursor-cloud-agents).

## Docker Desktop

1. Install [Docker Desktop](https://docs.docker.com/desktop/) for your platform.
2. On Windows, enable the **WSL2** backend (recommended).
3. Start Docker Desktop and wait until it reports that the engine is running.
4. Verify:

```bash
docker version
docker compose version
```

Both commands should succeed without connection errors.

## `just`

1. Install [`just`](https://github.com/casey/just#installation) for your platform (see the official install options for Windows, macOS, and Linux).
2. Verify:

```bash
just --version
```

## Next steps

With Docker Desktop and `just` installed:

1. Copy [`.env.example`](../.env.example) to `.env` and set local values (see [local-development.md — Environment configuration](local-development.md#environment-configuration)).
2. Continue with [local-development.md](local-development.md) for app vs sandbox lifecycle (`just up`, recipes).

List recipes with `just`; definitions live in [justfile](../justfile). Do not add further host tooling for this project.

Agent CLI policy (never host `uv` / `python` / raw `docker compose`): [AGENTS.md](../AGENTS.md).
