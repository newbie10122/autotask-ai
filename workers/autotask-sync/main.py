from workers.shared.worker_base import env_int, log, run_forever
from app.operations import run_due_jobs


def recent_sync_job() -> None:
    results = run_due_jobs(only={"recent_sync"})
    if results:
        log(f"recent sync scheduler results: {results}")


def job() -> None:
    recent_sync_job()


run_forever("worker-sync", env_int("SYNC_RECENT_INTERVAL_MINUTES", 15) * 60, job)
