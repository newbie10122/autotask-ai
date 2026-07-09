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
    assert "EMBED_NOISE_CHUNKS=false" in example
    assert "host.docker.internal" in docs


def test_raw_sync_tmux_scripts_and_docs_are_present():
    script_names = (
        "start-raw-sync-tmux.sh",
        "raw-sync-loop.sh",
        "raw-sync-status.sh",
        "stop-raw-sync.sh",
    )
    for script_name in script_names:
        script = ROOT / "scripts" / script_name
        assert script.exists()
        assert script.stat().st_mode & 0o111
        text = script.read_text()
        assert "set -x" not in text
        assert "cat .env" not in text

    reclassify = ROOT / "scripts" / "reclassify-chunks.sh"
    assert "reclassify_chunks" in reclassify.read_text()
    assert (ROOT / "scripts" / "sync-reference-data.sh").exists()
    assert (ROOT / "scripts" / "classify-tickets.sh").exists()

    runbook = (ROOT / "docs" / "FIRST_SYNC_RUNBOOK.md").read_text()
    assert "autotask-ai-sync" in runbook
    assert "./scripts/raw-sync-status.sh" in runbook
    assert "./scripts/stop-raw-sync.sh" in runbook


def test_ticket_analytics_migration_adds_classification_and_reference_schema():
    migration = (ROOT / "apps" / "api" / "migrations" / "005_ticket_analytics_classification.sql").read_text()
    assert "ADD COLUMN IF NOT EXISTS ticket_class" in migration
    assert "ADD COLUMN IF NOT EXISTS analytics_exclude" in migration
    assert "CREATE TABLE IF NOT EXISTS autotask_reference_values" in migration
    assert "CREATE INDEX IF NOT EXISTS autotask_tickets_issue_class_idx" in migration


def test_operations_scheduler_schema_and_worker_are_present():
    migration = (ROOT / "apps" / "api" / "migrations" / "006_operations_scheduler.sql").read_text()
    assert "CREATE TABLE IF NOT EXISTS scheduled_jobs" in migration
    assert "CREATE TABLE IF NOT EXISTS job_runs" in migration
    assert "CREATE TABLE IF NOT EXISTS job_locks" in migration
    assert (ROOT / "workers" / "scheduler" / "main.py").exists()
    assert (ROOT / "workers" / "scheduler" / "Dockerfile").exists()
    compose = (ROOT / "docker-compose.yml").read_text()
    assert "worker-scheduler:" in compose


def test_compose_config_uses_redacted_wrapper_only():
    wrapper = ROOT / "scripts" / "compose-config-redacted.sh"
    assert wrapper.exists()
    assert wrapper.stat().st_mode & 0o111
    assert "docker compose config" in wrapper.read_text()

    allowed_warning = "Never run raw docker compose config"
    offenders: list[str] = []
    for directory in (ROOT / "docs", ROOT / "scripts"):
        for path in directory.rglob("*"):
            if not path.is_file() or path == wrapper:
                continue
            if path.suffix not in {".md", ".sh"}:
                continue
            for line_number, line in enumerate(path.read_text().splitlines(), start=1):
                if "docker compose config" in line and allowed_warning not in line:
                    offenders.append(f"{path.relative_to(ROOT)}:{line_number}")

    readme = ROOT / "README.md"
    assert allowed_warning in readme.read_text()
    assert "./scripts/compose-config-redacted.sh" in readme.read_text()
    assert allowed_warning in (ROOT / "docs" / "RAG_DESIGN.md").read_text()
    assert not offenders
