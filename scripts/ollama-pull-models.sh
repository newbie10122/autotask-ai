#!/usr/bin/env bash
set -euo pipefail

set -a
[ -f .env.example ] && . ./.env.example
[ -f .env ] && . ./.env
set +a

docker compose --profile llm up -d ollama
docker compose exec ollama ollama pull "${OLLAMA_CHAT_MODEL:-llama3.2:3b}"
docker compose exec ollama ollama pull "${OLLAMA_EMBEDDING_MODEL:-nomic-embed-text}"
