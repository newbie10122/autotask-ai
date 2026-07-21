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
- `ticket_note_gaps`
- `raw_backfill_time_entries`
- `ticket_time_entry_gaps`
- `open_ticket_time_entry_gaps`
- `raw_backfill_ticket_history`
- `targeted_waiting_ticket_history`
- `status_sample_ticket_history`
- `ticket_history_gaps`
- `open_ticket_history_gaps`
- `related_data_work_plan`
- `raw_backfill_companies`
- `sync_reference_data`
- `classify_tickets`
- `build_documents`
- `reclassify_chunks`
- `run_embeddings`
- `nightly_pipeline`
- `customer_success_score_snapshot`

## Default Safety

Defaults are conservative:

- Recent sync is enabled every 15 minutes.
- Recent sync pulls companies, tickets, ticket notes, and TimeEntries in bounded batches.
- Open-ticket TimeEntries and TicketHistory gap jobs are enabled every 15 minutes.
- Estate-wide TimeEntries and TicketHistory gap jobs are enabled hourly.
- Raw historical backfill and targeted/manual sampling jobs are disabled until an admin enables them.
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
- Related-data coverage for open-ticket and estate TimeEntries/TicketHistory.
- Running jobs with stop-request controls.
- Scheduled jobs with enable/disable controls.
- Run-now buttons for bounded maintenance jobs.
- Last 50 job runs with counts, duration, and errors.

## Recent Sync

`recent_sync` pulls small recent batches of companies, tickets, ticket notes, and TimeEntries. It does not automatically build documents or embeddings. Use this for normal low-impact freshness.

## Related Data Gaps

The scheduler continuously fills local TimeEntries and TicketHistory coverage without writing to Autotask:

- `open_ticket_time_entry_gaps` and `open_ticket_history_gaps` prioritize open tickets every 15 minutes.
- `ticket_time_entry_gaps` and `ticket_history_gaps` sweep the broader local ticket estate hourly.
- Raw backfill and targeted status-sampling jobs remain manual/bounded controls for catch-up work.

## Raw Backfill

Raw backfill is disabled by default. When enabled, ticket, note, time-entry, ticket-history, and company jobs run in configured batches. They do not trigger full embeddings.

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
