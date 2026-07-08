from __future__ import annotations

import argparse
import json

from .documents import create_documents_from_tickets
from .embeddings import run_embedding_batch
from .sync import sync_companies, sync_recent, sync_ticket_notes, sync_tickets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["companies", "tickets", "ticket-notes", "recent", "documents", "embeddings"])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--full-sync", action="store_true")
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
    else:
        result = run_embedding_batch(limit=args.limit)
    print(json.dumps(result, default=str, indent=2))


if __name__ == "__main__":
    main()
