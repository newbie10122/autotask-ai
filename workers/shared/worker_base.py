import os
import time
from datetime import UTC, datetime


def log(message: str) -> None:
    print(f"{datetime.now(UTC).isoformat()} {message}", flush=True)


def run_forever(worker_name: str, interval_seconds: int, job) -> None:
    log(f"{worker_name} started")
    while True:
        try:
            job()
        except Exception as exc:
            log(f"{worker_name} failed: {exc}")
        time.sleep(interval_seconds)


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default

