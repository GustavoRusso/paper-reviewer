FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.7.12 /uv /uvx /usr/local/bin/

# git: dlthub ai init / AI workbench. curl: Streamlit ui healthcheck and just install.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Same just version as the Cloud VM host image (.cursor/Dockerfile). In-container recipes need it.
ARG JUST_VERSION=1.58.0
RUN arch="$(uname -m)" \
    && case "$arch" in \
         x86_64) just_arch=x86_64 ;; \
         aarch64) just_arch=aarch64 ;; \
         *) echo "unsupported arch: $arch" >&2; exit 1 ;; \
       esac \
    && curl -sSfL "https://github.com/casey/just/releases/download/${JUST_VERSION}/just-${JUST_VERSION}-${just_arch}-unknown-linux-musl.tar.gz" \
    | tar -xz -C /usr/local/bin just \
    && just --version

WORKDIR /workspace

CMD ["sleep", "infinity"]
