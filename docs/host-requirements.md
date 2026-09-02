# Host requirements

Install these tools on your machine before any Paper Reviewer workflow. Do **not** install frameworks, languages, compilers, runtimes, or other app tooling on the host. Anything needed to develop or run the app must live inside Docker images.

## What belongs on the host

| Tool | Role | Required when |
| --- | --- | --- |
| **Docker Desktop** | Runs the product stack and the sandbox workspace in containers (WSL2 backend recommended on Windows). | Always |
| **`just`** | Single command interface for every project workflow. Testers use `just up`. Developers use `just up` / `just notebooks` / other host recipes from the host, and the same recipe names inside the image. | Always (including local develop) |
| **Cursor (or VS Code) + Dev Containers** | Attach the IDE to the sandbox Compose `workspace` service. Cursor ships Anysphere Dev Containers; VS Code needs the **Dev Containers** extension (`ms-vscode-remote.remote-containers`). [`.vscode/extensions.json`](../.vscode/extensions.json) recommends both. | Local develop (**Reopen in Container**) |

Cursor Cloud Agent VMs install Docker Engine and `just` from [`.cursor/environment.json`](../.cursor/environment.json). You do not install those tools by hand on the Cloud VM. See [local-development.md — Cursor Cloud](local-development.md#cursor-cloud).

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

Required for testers, local developers, and host recipes (`just up`, `just notebooks`, `just migrate`, `just sandbox` when you are not attached). Inside the workspace image, `just` is already installed.

1. Install [`just`](https://github.com/casey/just#installation) for your platform (see the official install options for Windows, macOS, and Linux).
2. Verify:

```bash
just --version
```

## Next steps

1. Copy [`.env.example`](../.env.example) to `.env` and set local values (see [local-development.md — Environment configuration](local-development.md#environment-configuration)).
2. On Windows, keep text as **LF** (see [local-development.md — Line endings](local-development.md#line-endings)): set the editor EOL to `\n`, and set host Git `core.autocrlf` to `input` or `false` (not `true`).
3. Choose a path:
   - **Run the product:** [local-development.md — Local: run the product](local-development.md#local-run-the-product) (`just up`).
   - **Develop:** [local-development.md — Local: develop](local-development.md#local-develop) (**Reopen in Container**).

List recipes with `just`; definitions live in [justfile](../justfile). Do not add further host tooling for this project.

Agent CLI policy: [AGENTS.md](../AGENTS.md).
