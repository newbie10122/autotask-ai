from workers.shared.worker_base import log, run_forever


def embedding_job() -> None:
    log("embedding placeholder: store vectors with source metadata for every chunk")


run_forever("worker-embeddings", 300, embedding_job)

