# Host requirements

Install these tools on your machine before any Paper Reviewer workflow. They are the **only** host requirements for the default path. The optional Dev Container path needs Docker Desktop and Cursor (or VS Code) with Dev Containers support; it does **not** need `just` on the host.

## What belongs on the host

| Tool | Role | Required when |
| --- | --- | --- |
| **Docker Desktop** | Runs the entire development and application stack in containers (WSL2 backend recommended on Windows). | Always |
| **`just`** | Single command interface for every project workflow on the host. | Host / `just` path (default for agents) |
| **Cursor (or VS Code) + Dev Containers** | Attach the IDE to the Compose `workspace` service. Cursor ships Anysphere Dev Containers; VS Code needs the **Dev Containers** extension (`ms-vscode-remote.remote-containers`). [`.vscode/extensions.json`](../.vscode/extensions.json) recommends both. | Optional Dev Container path only |

Do **not** install frameworks, languages, compilers, runtimes, or other app tooling on the host. Anything needed to develop or run the app must live inside Docker images.

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

Required for the host/`just` workflow (and for host agent shells per [AGENTS.md](../AGENTS.md)). Optional if you only use **Reopen in Container**.

1. Install [`just`](https://github.com/casey/just#installation) for your platform (see the official install options for Windows, macOS, and Linux).
2. Verify:

```bash
just --version
```

## Next steps

1. Copy [`.env.example`](../.env.example) to `.env` and set local values (see [local-development.md — Environment configuration](local-development.md#environment-configuration)).
2. On Windows, keep text as **LF** (see [local-development.md — Line endings](local-development.md#line-endings)): set the editor EOL to `\n`, and set host Git `core.autocrlf` to `input` or `false` (not `true`).
3. Choose a path:
   - **Host / `just`:** continue with [local-development.md](local-development.md) (`just up`, recipes).
   - **Dev Container:** see [local-development.md — Dev Containers](local-development.md#dev-containers) (`Reopen in Container`).

List recipes with `just`; definitions live in [justfile](../justfile). Do not add further host tooling for this project.

Agent CLI policy (host vs Dev Container): [AGENTS.md](../AGENTS.md).
