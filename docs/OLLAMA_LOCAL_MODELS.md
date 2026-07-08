# Ollama Local Models

Ollama is optional and internal-only. It is not published on a host port.

Start it intentionally:

```bash
docker compose --profile llm up -d ollama
```

Configure models in `.env`:

```dotenv
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_CHAT_MODEL=llama3.2:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

Pull configured models:

```bash
scripts/ollama-pull-models.sh
```

`nomic-embed-text` is the initial embedding model and stores 768-dimensional vectors in pgvector. The initial chat model should be small enough for CPU-only operation; adjust `OLLAMA_CHAT_MODEL` if the host has different capacity.
