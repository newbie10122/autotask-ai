# Operations Scheduler

The Operations scheduler removes the need to manually babysit sync and RAG maintenance scripts. Use the Admin Operations UI for normal work:

```text
http://127.0.0.1:3010/#operations
```

Scripts remain fallback and emergency admin tools.

## What It Runs

The scheduler wakes every 60 seconds and checks DB-backed settings. It records every start, skip, completion, and failure in `job_runs`, with current job state in `scheduled_jobs` and duplicate protection in `job_locks`.

Jobs:

- `recent_sync`
- `raw_backfill_tickets`
- `raw_backfill_ticket_notes`
- `raw_backfill_companies`
- `sync_reference_data`
- `classify_tickets`
- `build_documents`
- `reclassify_chunks`
- `run_embeddings`
- `nightly_pipeline`

## Default Safety

Defaults are conservative:

- Recent sync is enabled every 15 minutes.
- Raw historical backfill is disabled until an admin enables it.
- Document build is disabled until an admin enables it.
- Ticket and chunk classification are enabled in bounded batches.
- Embeddings are disabled until an admin enables quiet-hours batches.
- Nightly pipeline is enabled, but skips document build and embeddings unless those settings are enabled.
- All jobs stop when `global_pause=true`.
- Jobs skip when disk free is below `min_free_disk_gb`.
- Autotask jobs skip when threshold remaining is below `autotask_threshold_min_remaining`.

## Operations UI

The page shows:

- API, DB, Ollama, Autotask threshold, and disk status.
- Local counts for companies, tickets, notes, documents, chunks, noise, useful chunks, embeddings, and missing eligible embeddings.
- Running jobs with stop-request controls.
- Scheduled jobs with enable/disable controls.
- Run-now buttons for bounded maintenance jobs.
- Last 50 job runs with counts, duration, and errors.

## Recent Sync

`recent_sync` pulls small recent batches and does not automatically build documents or embeddings. Use this for normal low-impact freshness.

## Raw Backfill

Raw backfill is disabled by default. When enabled, ticket, note, and company jobs run in configured batches. They do not trigger full embeddings.

## Nightly Pipeline

The nightly pipeline runs once after `nightly_pipeline_time` when enabled:

1. Sync reference labels.
2. Classify tickets.
3. Build documents only if document build is enabled.
4. Reclassify chunks if chunk classification is enabled.
5. Run embeddings only if embeddings are enabled and the current time is inside quiet hours.

## Pause And Recovery

Use Pause in Admin Operations to set `global_pause=true`. Resume clears it. Failed jobs remain in history; review the error, fix the cause, and use the matching run-now button for a bounded retry.

## Embeddings

Embeddings use CPU-only Ollama on this host. Keep `embedding_enabled=false` until ready, then enable quiet-hours batches with small limits. Noise chunks remain skipped by default.

## Attachments

Attachment ingestion is still disabled in this pass. The scheduler only operates on raw Autotask records already supported by the app.

## Compose Validation

Never run raw docker compose config in this repo. Always run:

```bash
./scripts/compose-config-redacted.sh
```
