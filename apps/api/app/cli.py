from __future__ import annotations

import argparse
import json

from .documents import create_documents_from_tickets, reclassify_chunks
from .embeddings import run_embedding_batch
from .operations import job_runs, operations_jobs, operations_settings, operations_status, run_due_jobs, run_job
from .sync import sync_companies, sync_recent, sync_ticket_notes, sync_tickets
from .ticket_analytics import classify_tickets, recurring_issues_report, sync_reference_data, ticket_class_report


def _job_limit_overrides(job_name: str | None, limit: int | None) -> dict[str, int]:
    if not job_name or limit is None:
        return {}
    mapping = {
        "raw_backfill_tickets": "raw_backfill_batch_tickets",
        "raw_backfill_ticket_notes": "raw_backfill_batch_notes",
        "raw_backfill_companies": "raw_backfill_batch_tickets",
        "classify_tickets": "ticket_classification_batch_size",
        "build_documents": "document_build_batch_size",
        "reclassify_chunks": "chunk_reclassification_batch_size",
        "run_embeddings": "embedding_batch_size",
    }
    key = mapping.get(job_name)
    return {key: limit} if key else {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "companies",
            "tickets",
            "ticket-notes",
            "recent",
            "documents",
            "embeddings",
            "reclassify-chunks",
            "sync-reference-data",
            "classify-tickets",
            "ticket-class-report",
            "recurring-issues",
            "operations-status",
            "operations-jobs",
            "operations-runs",
            "operations-settings",
            "run-job",
            "run-due-jobs",
        ],
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--full-sync", action="store_true")
    parser.add_argument("--include-inactive", action="store_true")
    parser.add_argument("--job-name", default=None)
    args = parser.parse_args()

    if args.command == "companies":
        result = sync_companies(limit=args.limit, full_sync=args.full_sync)
    elif args.command == "tickets":
        result = sync_tickets(limit=args.limit, full_sync=args.full_sync)
    elif args.command == "ticket-notes":
        result = sync_ticket_notes(limit=args.limit, full_sync=args.full_sync)
    elif args.command == "recent":
        result = sync_recent(limit=args.limit)
    elif args.command == "documents":
        result = create_documents_from_tickets(limit=args.limit)
    elif args.command == "embeddings":
        result = run_embedding_batch(limit=args.limit)
    elif args.command == "reclassify-chunks":
        result = reclassify_chunks(limit=args.limit, include_inactive=args.include_inactive)
    elif args.command == "sync-reference-data":
        result = sync_reference_data()
    elif args.command == "classify-tickets":
        result = classify_tickets(limit=args.limit)
    elif args.command == "ticket-class-report":
        result = ticket_class_report()
    elif args.command == "recurring-issues":
        result = recurring_issues_report(limit=args.limit or 8)
    elif args.command == "operations-status":
        result = operations_status()
    elif args.command == "operations-jobs":
        result = operations_jobs()
    elif args.command == "operations-runs":
        result = job_runs(limit=args.limit or 50)
    elif args.command == "operations-settings":
        result = operations_settings()
    elif args.command == "run-due-jobs":
        result = run_due_jobs()
    else:
        if not args.job_name:
            raise SystemExit("--job-name is required for run-job")
        result = run_job(
            args.job_name,
            triggered_by="manual",
            force=True,
            setting_overrides=_job_limit_overrides(args.job_name, args.limit),
        )
    print(json.dumps(result, default=str, indent=2))


if __name__ == "__main__":
    main()
