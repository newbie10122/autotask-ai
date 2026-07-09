from workers.shared.worker_base import log, run_forever
from app.operations import run_due_jobs


def document_extraction_job() -> None:
    results = run_due_jobs(only={"build_documents"})
    if results:
        log(f"document scheduler results: {results}")


run_forever("worker-documents", 300, document_extraction_job)
