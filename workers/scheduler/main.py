from datetime import UTC, datetime

from workers.shared.worker_base import env_int, log, run_forever
from app.operations import record_scheduler_heartbeat, run_due_jobs


WORKER_NAME = "worker-scheduler"
INTERVAL_SECONDS = env_int("SCHEDULER_INTERVAL_SECONDS", 60)


def scheduler_job() -> None:
    tick_started_at = datetime.now(UTC)
    record_scheduler_heartbeat(
        WORKER_NAME,
        interval_seconds=INTERVAL_SECONDS,
        status="running",
        tick_started_at=tick_started_at,
    )
    try:
        results = run_due_jobs()
    except Exception as exc:
        record_scheduler_heartbeat(
            WORKER_NAME,
            interval_seconds=INTERVAL_SECONDS,
            status="failed",
            last_error=str(exc),
            tick_started_at=tick_started_at,
            tick_finished_at=datetime.now(UTC),
        )
        raise
    tick_finished_at = datetime.now(UTC)
    record_scheduler_heartbeat(
        WORKER_NAME,
        interval_seconds=INTERVAL_SECONDS,
        status="running",
        tick_started_at=tick_started_at,
        tick_finished_at=tick_finished_at,
    )
    if results:
        log(f"scheduler results: {results}")


run_forever(WORKER_NAME, INTERVAL_SECONDS, scheduler_job)
