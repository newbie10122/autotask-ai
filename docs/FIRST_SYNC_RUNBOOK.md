# First Sync Runbook

## Verify `.env`

Confirm these keys are set in `/opt/apps/autotask-ai/.env`: `AUTOTASK_BASE_URL`, `AUTOTASK_USERNAME`, `AUTOTASK_SECRET`, `AUTOTASK_API_INTEGRATION_CODE`, `AUTOTASK_PAGE_SIZE=500`, and `AUTOTASK_SYNC_BATCH_LIMIT=500`.

Do not print `.env` in shared logs or tickets.

## Start and Check the Stack

```bash
docker compose up -d --build
curl http://127.0.0.1:5110/health
curl http://127.0.0.1:5110/ready
```

## Test Threshold

```bash
curl http://127.0.0.1:5110/api/autotask/threshold
```

## Run Safe Initial Syncs

```bash
scripts/sync-companies.sh --limit 25
scripts/sync-tickets.sh --limit 25
scripts/sync-ticket-notes.sh --limit 25
```

Use `--full-sync` only when ready for a complete historical pull.

## Build Documents

```bash
scripts/build-documents.sh --limit 100
```

## Run Embeddings

Start Ollama and pull models first:

```bash
docker compose --profile llm up -d ollama
scripts/ollama-pull-models.sh
scripts/run-embeddings.sh --limit 16
```

If Ollama or a model is missing, the embedding worker records a graceful failure and can be rerun.

## Ask a Test Question

```bash
curl -X POST http://127.0.0.1:5110/api/assistant/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"What has fixed VPN connection failures before?","mode":"ticket_history_only","limit":5}'
```

## Check Logs and Status

```bash
scripts/status.sh
scripts/logs.sh
curl http://127.0.0.1:5110/api/sync/status
curl http://127.0.0.1:5110/api/sync/runs
```

## Stop the Stack

```bash
docker compose down
```

## Resume After Failure

Rerun the same sync script. Completed runs store `last_seen_id` checkpoints, so default runs resume from the latest completed checkpoint. If a failed run stopped before completion, rerun with the same limit to continue safely.
