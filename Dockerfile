FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.7.12 /uv /uvx /usr/local/bin/

# git: dlthub ai init / AI workbench. curl: Streamlit ui healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

CMD ["sleep", "infinity"]
