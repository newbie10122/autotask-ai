# Ollama Local Models

Ollama can run either as a Compose profile service or directly on the host OS. On this deployment, Ollama runs on the host OS and listens on `127.0.0.1:11434`.

When Ollama runs on the host OS, containers cannot use `127.0.0.1` because that points back to each container. Configure `.env` to use Docker's host gateway name:

```dotenv
OLLAMA_BASE_URL=http://host.docker.internal:11434
LOCAL_LLM_BASE_URL=http://host.docker.internal:11434
OLLAMA_CHAT_MODEL=qwen2.5-coder:7b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_MODEL_NAME=nomic-embed-text
```

The Compose services that call Ollama must also include:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

This mapping is required on Linux so `host.docker.internal` resolves to the host gateway from inside the containers.

If the host firewall uses a default-deny policy, allow Docker bridge subnets to reach Ollama on the host. For UFW, use a persistent rule like:

```bash
sudo ufw allow in from 172.16.0.0/12 to any port 11434 proto tcp
```

Keep this scoped to the Docker private address range and the Ollama port; do not publish Ollama through the app's public Nginx site.

If you prefer the optional Compose-managed Ollama service instead, start it intentionally:

```bash
docker compose --profile llm up -d ollama
```

For Compose-managed Ollama, use:

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
