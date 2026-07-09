from workers.shared.worker_base import log, run_forever
from app.operations import run_due_jobs


def embedding_job() -> None:
    results = run_due_jobs(only={"run_embeddings"})
    if results:
        log(f"embedding scheduler results: {results}")


run_forever("worker-embeddings", 300, embedding_job)
