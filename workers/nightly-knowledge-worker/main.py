from workers.shared.worker_base import log, run_forever
from app.operations import run_due_jobs


def nightly_repair_and_summarization_job() -> None:
    results = run_due_jobs(only={"nightly_pipeline"})
    if results:
        log(f"nightly scheduler results: {results}")


run_forever("worker-nightly", 3600, nightly_repair_and_summarization_job)
