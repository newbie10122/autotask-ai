from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[3]


def test_env_is_ignored_and_example_is_present():
    gitignore = (ROOT / ".gitignore").read_text()
    assert ".env" in gitignore
    assert "!/.env.example" not in gitignore
    assert (ROOT / ".env.example").exists()


def test_ci_workflow_runs_safe_repository_validation():
    workflow = ROOT / ".github" / "workflows" / "ci.yml"
    validator = ROOT / "scripts" / "validate-ci.sh"
    docs = ROOT / "docs" / "CI_VALIDATION.md"

    assert workflow.exists()
    assert validator.exists()
    assert docs.exists()
    assert validator.stat().st_mode & 0o111

    workflow_text = workflow.read_text()
    validator_text = validator.read_text()
    docs_text = docs.read_text()

    assert "pull_request:" in workflow_text
    assert "workflow_dispatch:" in workflow_text
    assert "contents: read" in workflow_text
    assert "./scripts/validate-ci.sh" in workflow_text
    assert "docker compose config" not in workflow_text

    assert "./scripts/compose-config-redacted.sh" in validator_text
    assert "docker compose build api" in validator_text
    assert "python -m compileall -q apps/api/app workers" in validator_text
    assert "pytest -q" in validator_text
    assert "mktemp --suffix=.js" in validator_text
    assert "node --check" in validator_text
    assert "migration does not use NNN_name.sql format" in validator_text
    assert "cat .env" not in validator_text
    assert "set -x" not in validator_text

    assert "./scripts/validate-ci.sh" in docs_text
    assert "Capability Certification Receipt" in docs_text
    assert "Autotask write-back" in docs_text
    assert "must be `none`" in docs_text


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


def test_analytics_does_not_show_raw_unmapped_reference_ids():
    analytics = (ROOT / "apps" / "api" / "app" / "ticket_analytics.py").read_text()
    assert "is unmapped" not in analytics
    assert "redact_private_entities" in analytics


def test_web_dashboard_does_not_show_autotask_account_identity():
    web = (ROOT / "apps" / "web" / "index.html").read_text()
    assert "autotaskUser" not in web
    assert "Base URL" not in web
    assert "<span>Username</span>" not in web


def test_operations_scheduler_schema_and_worker_are_present():
    migration = (ROOT / "apps" / "api" / "migrations" / "006_operations_scheduler.sql").read_text()
    assert "CREATE TABLE IF NOT EXISTS scheduled_jobs" in migration
    assert "CREATE TABLE IF NOT EXISTS job_runs" in migration
    assert "CREATE TABLE IF NOT EXISTS job_locks" in migration
    db_schema = (ROOT / "apps" / "api" / "app" / "db.py").read_text()
    assert "CREATE TABLE IF NOT EXISTS autotask_time_entries" in db_schema
    assert "CREATE TABLE IF NOT EXISTS autotask_ticket_history" in db_schema
    assert "CREATE TABLE IF NOT EXISTS ticket_gap_sync_checks" in db_schema
    assert (ROOT / "workers" / "scheduler" / "main.py").exists()
    assert (ROOT / "workers" / "scheduler" / "Dockerfile").exists()
    nightly = (ROOT / "workers" / "nightly-knowledge-worker" / "Dockerfile").read_text()
    assert "COPY apps/api/app ./app" in nightly
    compose = (ROOT / "docker-compose.yml").read_text()
    assert "worker-scheduler:" in compose


def test_nginx_http_preview_helper_and_docs_are_present():
    script = ROOT / "scripts" / "install-nginx-http-preview.sh"
    assert script.exists()
    assert script.stat().st_mode & 0o111
    script_text = script.read_text()
    assert "/etc/nginx/.helix-preview-auth" in script_text
    assert "/etc/nginx/sites-available/autotask-ai" in script_text
    assert "proxy_read_timeout 180s" in script_text
    assert "certbot" not in script_text
    assert "docker compose config" not in script_text

    docs = (ROOT / "docs" / "NGINX_HTTP_PREVIEW.md").read_text()
    assert "HTTP-only" in docs
    assert "Basic Auth" in docs
    assert "not encrypted without HTTPS" in docs
    assert "/etc/nginx/sites-available/autotask-ai" in docs
    assert "127.0.0.1:3010" in docs
    assert "127.0.0.1:5110" in docs


def test_compose_config_uses_redacted_wrapper_only():
    wrapper = ROOT / "scripts" / "compose-config-redacted.sh"
    assert wrapper.exists()
    assert wrapper.stat().st_mode & 0o111
    assert "docker compose config" in wrapper.read_text()

    allowed_warning = "Never run raw docker compose config"

    def is_allowed_warning(line: str) -> bool:
        return allowed_warning in line or ("Never run raw" in line and "docker compose config" in line)

    offenders: list[str] = []
    for directory in (ROOT / "docs", ROOT / "scripts"):
        for path in directory.rglob("*"):
            if not path.is_file() or path == wrapper:
                continue
            if path.suffix not in {".md", ".sh"}:
                continue
            for line_number, line in enumerate(path.read_text().splitlines(), start=1):
                if "docker compose config" in line and not is_allowed_warning(line):
                    offenders.append(f"{path.relative_to(ROOT)}:{line_number}")

    readme = ROOT / "README.md"
    assert allowed_warning in readme.read_text()
    assert "./scripts/compose-config-redacted.sh" in readme.read_text()
    assert allowed_warning in (ROOT / "docs" / "RAG_DESIGN.md").read_text()
    assert not offenders
