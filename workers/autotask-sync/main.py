from workers.shared.worker_base import env_int, log, run_forever


def historical_sync_job() -> None:
    log("historical sync placeholder: resumable 500-record Autotask pages, read-only")


def recent_sync_job() -> None:
    log("recent 15-minute sync placeholder: no live question path calls Autotask")


def job() -> None:
    historical_sync_job()
    recent_sync_job()


run_forever("worker-sync", env_int("SYNC_RECENT_INTERVAL_MINUTES", 15) * 60, job)

