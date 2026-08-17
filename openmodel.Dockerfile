# Gateway image: OpenModel CLI + Ollama client binary (talks to the ollama service).
FROM ollama/ollama:latest AS ollama

FROM node:20-slim

COPY --from=ollama /bin/ollama /usr/local/bin/ollama

RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates \
  && rm -rf /var/lib/apt/lists/* \
  && npm install --global @wundercorp/openmodel

EXPOSE 11435

CMD ["om", "serve", "--host", "0.0.0.0", "--port", "11435"]