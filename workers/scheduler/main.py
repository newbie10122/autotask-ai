from workers.shared.worker_base import env_int, log, run_forever
from app.operations import run_due_jobs


def scheduler_job() -> None:
    results = run_due_jobs()
    if results:
        log(f"scheduler results: {results}")


run_forever("worker-scheduler", env_int("SCHEDULER_INTERVAL_SECONDS", 60), scheduler_job)
