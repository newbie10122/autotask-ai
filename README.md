# Autotask AI

Internal CompuOne technician assistant for local Autotask ticket-history ingestion, pgvector search, and CPU-only Ollama RAG assistance.

This MVP foundation is internal-only, read-only into Autotask, and designed to run behind existing Nginx Basic Auth on `helix-prod-01`. The app binds to localhost ports only: web on `127.0.0.1:3010` and API on `127.0.0.1:5110`. PostgreSQL and the optional local LLM service are not published publicly.

## Structure

- `apps/web` static web portal shell
- `apps/api` FastAPI backend shell
- `workers/autotask-sync` recent sync worker using the same read-only sync services as the API
- `workers/document-worker` ticket and note document creation
- `workers/embedding-worker` Ollama embedding worker
- `workers/nightly-knowledge-worker` nightly repair/summarization placeholder
- `apps/api/migrations` PostgreSQL and pgvector schema
- `nginx` sample reverse proxy with Basic Auth
- `scripts` deployment, update, logs, status, backup, and restore helpers

## Local Setup

```bash
cp .env.example .env
chmod +x scripts/*.sh
docker compose up -d --build
curl http://127.0.0.1:5110/health
```

Open the web shell at `http://127.0.0.1:3010`.

## Compose Validation Safety

Never run raw docker compose config in this repo. Always run:

```bash
./scripts/compose-config-redacted.sh
```

The wrapper redacts secret-like environment values before printing Compose validation output.

Start local Ollama intentionally when needed:

```bash
docker compose --profile llm up -d ollama
scripts/ollama-pull-models.sh
```

## Production Deployment

On `helix-prod-01`:

```bash
cd /opt/apps/autotask-ai
cp .env.example .env
$EDITOR .env
chmod +x scripts/*.sh
scripts/production-auth-preflight.sh .env
scripts/deploy.sh
```

Install the sample Nginx config:

```bash
sudo cp nginx/autotask-ai.conf /etc/nginx/sites-available/autotask-ai.conf
sudo ln -s /etc/nginx/sites-available/autotask-ai.conf /etc/nginx/sites-enabled/autotask-ai.conf
sudo htpasswd -c /etc/nginx/.htpasswd-autotask-ai admin
sudo nginx -t
sudo systemctl reload nginx
```

Update `server_name` and TLS certificate paths in `nginx/autotask-ai.conf` before enabling it.

For production, app-route auth must be enabled with `APP_ROUTE_AUTH_REQUIRED=true` unless an approved external authentication boundary is explicitly recorded in `.env` with `EXTERNAL_AUTH_CONFIRMED=true` and `EXTERNAL_AUTH_DESCRIPTION`.

## API

- `GET /health`
- `GET /ready`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /settings`
- `GET /audit-log`
- `POST /autotask/test-connection`
- `GET /api/autotask/threshold`
- `POST /api/autotask/test/companies`
- `POST /api/autotask/test/tickets`
- `POST /api/autotask/test/ticket-notes`
- `POST /api/sync/companies/start`
- `POST /api/sync/tickets/start`
- `POST /api/sync/ticket-notes/start`
- `POST /api/sync/recent/start`
- `GET /api/sync/status`
- `GET /api/sync/runs`
- `POST /api/documents/build`
- `POST /api/embeddings/run`
- `POST /api/assistant/ask`
- `POST /api/assistant/feedback`
- `GET /api/operations/status`
- `GET /api/operations/settings`
- `POST /api/operations/settings`
- `GET /api/operations/jobs`
- `GET /api/operations/jobs/runs`
- `POST /api/operations/jobs/{job_name}/run`

## Autotask

Autotask credentials are read from `.env` and sent as `Username`, `Secret`, and `APIIntegrationcode` headers. See `docs/AUTOTASK_API_USER.md`.

The MVP does not implement Autotask create, update, delete, webhooks, or live question-time Autotask calls.

## Operations Scheduler

Normal sync, classification, document build, embedding batches, and job history are controlled from the Admin Operations UI. See `docs/OPERATIONS_SCHEDULER.md`.

Default scheduler settings are conservative: recent sync is enabled, historical raw backfill and document build are disabled, embeddings are disabled, and nightly work skips embeddings unless an admin enables them for quiet hours. Existing scripts remain available as fallback or emergency admin tools, but routine operation should use the Operations UI.

First safe pull:

```bash
scripts/sync-companies.sh --limit 25
scripts/sync-tickets.sh --limit 25
scripts/sync-ticket-notes.sh --limit 25
scripts/build-documents.sh --limit 25
scripts/run-embeddings.sh --limit 16
```

## Validation

Run the same validation used by CI with:

```bash
./scripts/validate-ci.sh
```

This performs redacted Compose validation, migration ordering checks, API image build, Python compilation, full pytest, and static web JavaScript syntax validation. See `docs/CI_VALIDATION.md`.

## RAG Guardrails

Answers must separate internal evidence from general guidance, and saved fixes become pending memory candidates only. See `docs/RAG_DESIGN.md`.

## Tests

The Python tests cover health endpoints, auth model/audit logging, answer format guardrails, Autotask write-call blocking, and repo hygiene.

```bash
cd apps/api
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pytest
```
