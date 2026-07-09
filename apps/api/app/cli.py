from __future__ import annotations

import argparse
import json

from .documents import create_documents_from_tickets, reclassify_chunks
from .embeddings import run_embedding_batch
from .sync import sync_companies, sync_recent, sync_ticket_notes, sync_tickets
from .ticket_analytics import classify_tickets, recurring_issues_report, sync_reference_data, ticket_class_report


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
        ],
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--full-sync", action="store_true")
    parser.add_argument("--include-inactive", action="store_true")
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
    else:
        result = recurring_issues_report(limit=args.limit or 8)
    print(json.dumps(result, default=str, indent=2))


if __name__ == "__main__":
    main()
