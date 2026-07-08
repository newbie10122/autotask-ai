from workers.shared.worker_base import env_int, log, run_forever
from app.sync import sync_recent


def historical_sync_job() -> None:
    log("historical sync is manual-first; use scripts/sync-companies.sh and scripts/sync-tickets.sh for controlled initial pulls")


def recent_sync_job() -> None:
    result = sync_recent(limit=100)
    log(f"recent sync completed: {result}")


def job() -> None:
    historical_sync_job()
    recent_sync_job()


run_forever("worker-sync", env_int("SYNC_RECENT_INTERVAL_MINUTES", 15) * 60, job)
