from __future__ import annotations

import httpx

from .config import settings


class OllamaUnavailable(RuntimeError):
    pass


def embed_text(text: str, model: str | None = None) -> list[float]:
    try:
        response = httpx.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/embeddings",
            json={"model": model or settings.ollama_embedding_model, "prompt": text},
            timeout=60,
        )
        response.raise_for_status()
        embedding = response.json().get("embedding")
        if not isinstance(embedding, list):
            raise OllamaUnavailable("Ollama embedding response did not contain an embedding.")
        return [float(value) for value in embedding]
    except Exception as exc:
        raise OllamaUnavailable(str(exc)) from exc


def chat(prompt: str, model: str | None = None) -> str:
    try:
        response = httpx.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/generate",
            json={"model": model or settings.ollama_chat_model, "prompt": prompt, "stream": False},
            timeout=settings.deep_dive_timeout_seconds,
        )
        response.raise_for_status()
        return str(response.json().get("response") or "")
    except Exception as exc:
        raise OllamaUnavailable(str(exc)) from exc
