from workers.shared.worker_base import log, run_forever
from app.embeddings import run_embedding_batch


def embedding_job() -> None:
    result = run_embedding_batch()
    log(f"embedding batch completed: {result}")


run_forever("worker-embeddings", 300, embedding_job)
