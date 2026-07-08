from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[3]


def test_env_is_ignored_and_example_is_present():
    gitignore = (ROOT / ".gitignore").read_text()
    assert ".env" in gitignore
    assert "!/.env.example" not in gitignore
    assert (ROOT / ".env.example").exists()


def test_no_obvious_secret_values_committed():
    example = (ROOT / ".env.example").read_text()
    assert "change-me" in example
    assert not re.search(r"\bsk-[A-Za-z0-9]{20,}\b", example)
    assert "AKIA" not in example


def test_host_ollama_mapping_is_documented_for_required_services():
    compose = (ROOT / "docker-compose.yml").read_text()
    example = (ROOT / ".env.example").read_text()
    docs = (ROOT / "docs" / "OLLAMA_LOCAL_MODELS.md").read_text()

    for service in ("api", "worker-embeddings", "worker-nightly"):
        assert re.search(
            rf"  {service}:\n(?:    .+\n)*?    extra_hosts:\n      - \"host\.docker\.internal:host-gateway\"",
            compose,
        )
    assert "OLLAMA_BASE_URL=http://host.docker.internal:11434" in example
    assert "LOCAL_LLM_BASE_URL=http://host.docker.internal:11434" in example
    assert "OLLAMA_CHAT_MODEL=qwen2.5-coder:7b" in example
    assert "EMBEDDING_MODEL_NAME=nomic-embed-text" in example
    assert "host.docker.internal" in docs
