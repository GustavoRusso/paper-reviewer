FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.7.12 /uv /uvx /usr/local/bin/

WORKDIR /workspace

CMD ["sleep", "infinity"]
